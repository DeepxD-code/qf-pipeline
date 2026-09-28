import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;

/**
 * QF Java renderer: PNG cards -&gt; cinematic H.264 MP4 via system ffmpeg.
 *
 * <p>Pure JDK 21, zero dependencies. Ken Burns drift per segment (alternating
 * push-in/pull-out) + xfade melt cuts + optional QF_MUSIC bed. ffmpeg does the
 * encode (native code); this worker bounds it with Semaphore(2).
 *
 * <p>CLI usage: java -cp classes Compose &lt;images.txt&gt; &lt;out.mp4&gt; &lt;secsPerImage&gt; &lt;fps&gt;
 * In-process usage (Java backend): {@link #compose(List, Path, String, String)}.
 */
public final class Compose {

    private static final double XFADE = 0.5;

    private Compose() {}

    public static void main(String[] args) throws Exception {
        if (args.length < 4) {
            System.err.println("usage: Compose <images.txt> <out.mp4> <secsPerImage> <fps>");
            System.exit(2);
        }
        Path listFile = Path.of(args[0]);
        List<String> images = Files.readAllLines(listFile).stream()
                .map(String::trim).filter(s -> !s.isEmpty()).toList();
        if (images.isEmpty()) {
            System.err.println("no images listed in " + listFile);
            System.exit(2);
        }
        compose(images, Path.of(args[1]), args[2], args[3]);
        System.out.println("wrote " + args[1]);
    }

    public static void compose(List<String> images, Path out, String secs, String fps) throws Exception {
        double spi = Double.parseDouble(secs);
        int frames = Math.max(1, (int) (spi * Integer.parseInt(fps)));
        Files.createDirectories(out.toAbsolutePath().getParent());
        Path tmp = Files.createTempDirectory("qf-java-");
        try {
            Semaphore cpu = new Semaphore(2); // bound concurrent ffmpeg encodes
            List<Path> segs = new ArrayList<>();
            for (int i = 0; i < images.size(); i++) {
                segs.add(tmp.resolve(String.format("seg_%02d.mp4", i)));
            }
            try (var pool = Executors.newVirtualThreadPerTaskExecutor()) {
                List<java.util.concurrent.Future<?>> futures = new ArrayList<>();
                for (int i = 0; i < images.size(); i++) {
                    final int idx = i;
                    futures.add(pool.submit(() -> {
                        cpu.acquire();
                        try {
                            String zoom = idx % 2 == 0
                                    ? "1+0.15*on/" + frames
                                    : "1.15-0.15*on/" + frames;
                            run(List.of("ffmpeg", "-y",
                                    "-loop", "1", "-framerate", fps, "-i", images.get(idx),
                                    "-vf", "scale=2160:3840,zoompan=z='" + zoom
                                            + "':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                                            + ":d=" + frames + ":s=1080x1920:fps=" + fps + ",format=yuv420p",
                                    "-t", secs,
                                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                                    segs.get(idx).toString()));
                        } finally {
                            cpu.release();
                        }
                        return null;
                    }));
                }
                for (var f : futures) {
                    f.get();
                }
            }
            Path chained = tmp.resolve("chained.mp4");
            double dur = spi;
            if (segs.size() == 1) {
                Files.copy(segs.get(0), chained);
            } else {
                List<String> cmd = new ArrayList<>(List.of("ffmpeg", "-y"));
                for (Path s : segs) {
                    cmd.addAll(List.of("-i", s.toString()));
                }
                StringBuilder fc = new StringBuilder();
                String cur = "[0:v]";
                for (int k = 1; k < segs.size(); k++) {
                    double off = Math.round((dur - XFADE) * 1000.0) / 1000.0;
                    fc.append(cur).append("[").append(k).append(":v]xfade=transition=fade:duration=")
                            .append(XFADE).append(":offset=").append(off).append("[x").append(k).append("];");
                    cur = "[x" + k + "]";
                    dur = Math.round((dur + spi - XFADE) * 1000.0) / 1000.0;
                }
                fc.deleteCharAt(fc.length() - 1);
                cmd.addAll(List.of("-filter_complex", fc.toString(), "-map", cur, "-pix_fmt", "yuv420p",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", chained.toString()));
                run(cmd);
            }
            String music = System.getenv().getOrDefault("QF_MUSIC", "").strip();
            if (!music.isEmpty() && Files.exists(Path.of(music))) {
                double total = Math.round(dur * 1000.0) / 1000.0;
                double fadeStart = Math.round((total - 1) * 1000.0) / 1000.0;
                run(List.of("ffmpeg", "-y", "-i", chained.toString(), "-i", music,
                        "-filter_complex",
                        "[1:a]atrim=0:" + total + ",asetpts=PTS-STARTPTS,afade=t=out:st=" + fadeStart + ":d=1[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
                        "-t", String.valueOf(total), out.toString()));
            } else {
                Files.copy(chained, out, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
            }
        } finally {
            deleteTree(tmp);
        }
    }

    private static void run(List<String> cmd) throws IOException, InterruptedException {
        ProcessBuilder pb = new ProcessBuilder(cmd).redirectErrorStream(true);
        Process p = pb.start();
        String log;
        try (var in = p.getInputStream()) {
            log = new String(in.readAllBytes());
        }
        boolean ok = p.waitFor(10, TimeUnit.MINUTES) && p.exitValue() == 0;
        if (!ok) {
            String tail = log.length() > 2000 ? log.substring(log.length() - 2000) : log;
            throw new IOException("ffmpeg failed (" + String.join(" ", cmd) + "): " + tail);
        }
    }

    private static void deleteTree(Path dir) {
        try (var walk = Files.walk(dir)) {
            walk.sorted(Comparator.reverseOrder())
                    .forEach(p -> { try { Files.deleteIfExists(p); } catch (IOException ignored) {} });
        } catch (IOException ignored) {}
    }
}
