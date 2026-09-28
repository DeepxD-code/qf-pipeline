package qf;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;
import java.util.concurrent.Semaphore;

/**
 * QF Java backend: single-service HTTP API + demo web + MP4 serving.
 *
 * <p>Pure JDK 21, zero dependencies: built-in HttpServer on virtual threads,
 * file-backed job store (same schema as the Python backend, shares
 * STORAGE_DIR), Java2D cards, ffmpeg compose via the java-renderer worker.
 * Run from the project root: {@code workers\java-backend\build.bat} then
 * {@code make run-java-api} (or {@code java -cp workers\java-backend\classes
 * qf.QfServer}).
 */
public final class QfServer {

    static double defaultSpi = 2.5;
    static Semaphore renderSem;
    static boolean ffmpegOk;
    static Path webIndex = Path.of("apps", "web", "index.html");

    private QfServer() {}

    public static void main(String[] args) throws Exception {
        String storage = env("STORAGE_DIR", "storage");
        defaultSpi = Double.parseDouble(env("SECS_PER_IMAGE", "2.5"));
        int maxRenders = Integer.parseInt(env("MAX_CONCURRENT_RENDERS", "2"));
        int port = Integer.parseInt(env("PORT", env("API_PORT", "8000")));
        Store.init(storage, maxRenders);
        renderSem = new Semaphore(Store.maxRenders);
        ffmpegOk = probeFfmpeg();
        System.out.println("qf-java storage=" + storage + " ffmpeg=" + (ffmpegOk ? "ok" : "MISSING"));

        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        server.createContext("/", QfServer::route);
        server.setExecutor(Executors.newVirtualThreadPerTaskExecutor());
        server.start();
        System.out.println("qf-java listening on " + port);
    }

    static String env(String k, String def) {
        String v = System.getenv(k);
        return v == null || v.isBlank() ? def : v.strip();
    }

    static boolean probeFfmpeg() {
        try {
            Process p = new ProcessBuilder("ffmpeg", "-version").redirectErrorStream(true).start();
            try (var in = p.getInputStream()) {
                in.readAllBytes();
            }
            return p.waitFor() == 0;
        } catch (Exception e) {
            return false;
        }
    }

    // ---- router ----

    static void route(HttpExchange ex) throws IOException {
        try {
            String method = ex.getRequestMethod();
            String path = ex.getRequestURI().getPath();
            if (method.equals("GET") && path.equals("/")) {
                if (Files.exists(webIndex)) {
                    sendFile(ex, 200, webIndex, "text/html; charset=utf-8");
                } else {
                    sendJson(ex, 200, Map.of("service", "qf-pipeline-java", "docs", "/api/v1/stats"));
                }
            } else if (method.equals("GET") && path.equals("/live")) {
                sendJson(ex, 200, Map.of("status", "healthy", "service", "qf-pipeline-java"));
            } else if (method.equals("GET") && (path.equals("/health") || path.equals("/ready"))) {
                health(ex);
            } else if (method.equals("GET") && path.equals("/metrics")) {
                sendJson(ex, 200, Map.of("qf_jobs_total", Store.list(1000).size()));
            } else if (method.equals("GET") && path.equals("/api/v1/jobs")) {
                sendJson(ex, 200, Map.of("jobs", Store.list(20)));
            } else if (method.equals("POST") && path.equals("/api/v1/jobs")) {
                createJob(ex);
            } else if (method.equals("GET") && path.equals("/api/v1/stats")) {
                stats(ex);
            } else if (method.equals("GET") && path.startsWith("/api/v1/jobs/")) {
                getJob(ex, path.substring("/api/v1/jobs/".length()));
            } else if (method.equals("GET") && path.startsWith("/v/") && path.endsWith(".mp4")) {
                serveVideo(ex, path.substring(3, path.length() - 4));
            } else {
                sendJson(ex, 404, Map.of("detail", "not found"));
            }
        } catch (Exception e) {
            sendJson(ex, 500, Map.of("detail", "internal error: " + e));
        }
    }

    static void health(HttpExchange ex) throws IOException {
        boolean writable = true;
        try {
            Path probe = Store.root.resolve("jobs").resolve(".writetest");
            Files.writeString(probe, "ok", StandardCharsets.UTF_8);
            Files.deleteIfExists(probe);
        } catch (Exception e) {
            writable = false;
        }
        boolean ok = writable && ffmpegOk;
        Map<String, Object> checks = new LinkedHashMap<>();
        checks.put("storage", writable ? "ok" : "not writable");
        checks.put("ffmpeg", ffmpegOk ? "ok" : "missing");
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("status", ok ? "healthy" : "unhealthy");
        body.put("checks", checks);
        sendJson(ex, ok ? 200 : 503, body);
    }

    static void stats(HttpExchange ex) throws IOException {
        List<Map<String, Object>> jobs = Store.list(1000);
        Map<String, Object> byStatus = new LinkedHashMap<>();
        for (Map<String, Object> j : jobs) {
            String s = String.valueOf(j.getOrDefault("status", "?"));
            byStatus.put(s, ((Number) byStatus.getOrDefault(s, 0)).intValue() + 1);
        }
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("total", jobs.size());
        body.put("by_status", byStatus);
        body.put("backend", Map.of("visuals", "cards", "composer", "java"));
        body.put("max_concurrent_renders", Store.maxRenders);
        sendJson(ex, 200, body);
    }

    static void createJob(HttpExchange ex) throws IOException {
        String body = readBody(ex, 64 * 1024);
        String topic;
        Double spi = null;
        try {
            Map<String, Object> data = Json.obj(Json.parse(body));
            if (data == null) {
                throw new IllegalArgumentException("bad json");
            }
            topic = data.get("topic") == null ? "" : String.valueOf(data.get("topic")).strip();
            if (data.get("secs_per_image") instanceof Number n) {
                spi = n.doubleValue();
            }
        } catch (Exception e) {
            sendJson(ex, 422, Map.of("detail", "invalid JSON body"));
            return;
        }
        if (topic.length() < 3 || topic.length() > 300) {
            sendJson(ex, 422, Map.of("detail", "topic must be 3..300 chars"));
            return;
        }
        if (spi != null && (spi < 1.0 || spi > 6.0)) {
            sendJson(ex, 422, Map.of("detail", "secs_per_image must be 1.0..6.0"));
            return;
        }
        Map<String, Object> hit = Store.findReady(topic);
        if (hit != null) {
            Map<String, Object> res = new LinkedHashMap<>();
            res.put("job_id", hit.get("id"));
            res.put("status", "ready");
            res.put("cached", true);
            sendJson(ex, 202, res);
            return;
        }
        Map<String, Object> job = Store.newJob(topic);
        final String id = (String) job.get("id");
        final Double jobSpi = spi;
        Thread.ofVirtual().start(() -> runJob(id, jobSpi));
        Map<String, Object> res = new LinkedHashMap<>();
        res.put("job_id", id);
        res.put("status", "queued");
        res.put("cached", false);
        sendJson(ex, 202, res);
    }

    static void getJob(HttpExchange ex, String id) throws IOException {
        if (!id.matches("[A-Za-z0-9_-]+")) {
            sendJson(ex, 404, Map.of("detail", "job not found"));
            return;
        }
        Map<String, Object> job = Store.get(id);
        if (job == null) {
            sendJson(ex, 404, Map.of("detail", "job not found"));
            return;
        }
        sendJson(ex, 200, job);
    }

    static void serveVideo(HttpExchange ex, String id) throws IOException {
        if (!id.matches("[A-Za-z0-9_-]+") || !Files.exists(Store.videoPath(id))) {
            sendJson(ex, 404, Map.of("detail", "video not ready"));
            return;
        }
        ex.getResponseHeaders().set("Content-Type", "video/mp4");
        ex.getResponseHeaders().set("Content-Disposition", "attachment; filename=\"qoneqt-" + id + ".mp4\"");
        sendFile(ex, 200, Store.videoPath(id), "video/mp4");
    }

    // ---- pipeline ----

    static void runJob(String jobId, Double secsPerImage) {
        try {
            renderSem.acquire();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return;
        }
        try {
            runJobSync(jobId, secsPerImage);
        } finally {
            renderSem.release();
        }
    }

    @SuppressWarnings("unchecked")
    static void runJobSync(String jobId, Double secsPerImage) {
        Map<String, Object> job = Store.get(jobId);
        if (job == null) {
            return;
        }
        double spi = secsPerImage != null ? secsPerImage : defaultSpi;
        try {
            Map<String, Object> hit = Store.findReady((String) job.get("topic"));
            if (hit != null && !hit.get("id").equals(jobId)) {
                job.put("status", "ready");
                job.put("stage", "ready");
                job.put("script", hit.get("script"));
                Store.save(job);
                Files.copy(Store.videoPath((String) hit.get("id")), Store.videoPath(jobId),
                        java.nio.file.StandardCopyOption.REPLACE_EXISTING);
                job.put("video_url", "/v/" + jobId + ".mp4");
                Store.save(job);
                return;
            }
            job.put("status", "running");
            job.put("stage", "scripting");
            Store.save(job);
            Map<String, Object> script = Script.generate((String) job.get("topic"));
            for (Object o : (List<Object>) script.get("scenes")) {
                ((Map<String, Object>) o).put("duration_s", spi);
            }
            job.put("script", script);
            job.put("stage", "visuals");
            Store.save(job);

            List<String> cards = Cards.render(script, Store.cardsDir(jobId), spi);
            job.put("stage", "composing");
            Store.save(job);
            composeViaRenderer(cards, Store.videoPath(jobId), spi);

            job.put("status", "ready");
            job.put("stage", "ready");
            job.put("video_url", "/v/" + jobId + ".mp4");
            Store.save(job);
        } catch (Exception e) {
            job.put("status", "failed");
            job.put("stage", "failed");
            job.put("error", String.valueOf(e.getMessage()));
            Store.save(job);
            e.printStackTrace();
        }
    }

    /** Shell out to workers/java-renderer (bounded Semaphore(2) inside). */
    static void composeViaRenderer(List<String> images, Path out, double spi) throws Exception {
        Path rendererClasses = rendererClassesDir();
        if (!Files.exists(rendererClasses.resolve("Compose.class"))) {
            throw new IllegalStateException(
                    "Java renderer not built — run workers/java-renderer/build.bat first");
        }
        Path listFile = out.toAbsolutePath().getParent().resolve("images.txt");
        Files.writeString(listFile, String.join("\n", images), StandardCharsets.UTF_8);
        String javaExe = Path.of(System.getProperty("java.home"), "bin",
                System.getProperty("os.name").toLowerCase().contains("win") ? "java.exe" : "java").toString();
        List<String> cmd = new ArrayList<>(List.of(javaExe, "-cp", rendererClasses.toString(),
                "Compose", listFile.toString(), out.toString(), String.valueOf(spi), "30"));
        ProcessBuilder pb = new ProcessBuilder(cmd).redirectErrorStream(true);
        Process p = pb.start();
        String log;
        try (var in = p.getInputStream()) {
            log = new String(in.readAllBytes(), StandardCharsets.UTF_8);
        }
        boolean ok = p.waitFor(10, java.util.concurrent.TimeUnit.MINUTES) && p.exitValue() == 0
                && Files.exists(out);
        if (!ok) {
            String tail = log.length() > 2000 ? log.substring(log.length() - 2000) : log;
            throw new IllegalStateException("java Compose failed: " + tail);
        }
    }

    static Path rendererClassesDir() throws Exception {
        String override = System.getenv("QF_RENDERER_CLASSES");
        if (override != null && !override.isBlank()) {
            return Path.of(override.strip());
        }
        Path here = Path.of(QfServer.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        Path base = Files.isDirectory(here) ? here : here.getParent();
        // <root>/workers/java-backend/classes -> <root>/workers/java-renderer/classes
        Path backendClasses = base;
        while (backendClasses != null && !backendClasses.getFileName().toString().equals("classes")) {
            backendClasses = backendClasses.getParent();
        }
        if (backendClasses != null) {
            Path candidate = backendClasses.getParent().getParent().resolve("java-renderer").resolve("classes");
            if (Files.exists(candidate)) {
                return candidate;
            }
        }
        return Path.of("workers", "java-renderer", "classes").toAbsolutePath();
    }

    // ---- http helpers ----

    static String readBody(HttpExchange ex, int max) throws IOException {
        byte[] raw = ex.getRequestBody().readNBytes(max + 1);
        if (raw.length > max) {
            throw new IOException("body too large");
        }
        return new String(raw, StandardCharsets.UTF_8);
    }

    static void sendJson(HttpExchange ex, int code, Object body) throws IOException {
        byte[] raw = Json.stringify(body).getBytes(StandardCharsets.UTF_8);
        ex.getResponseHeaders().set("Content-Type", "application/json");
        ex.sendResponseHeaders(code, raw.length);
        try (var os = ex.getResponseBody()) {
            os.write(raw);
        }
    }

    static void sendFile(HttpExchange ex, int code, Path file, String contentType) throws IOException {
        long len = Files.size(file);
        ex.getResponseHeaders().set("Content-Type", contentType);
        ex.sendResponseHeaders(code, len);
        try (var os = ex.getResponseBody()) {
            Files.copy(file, os);
        }
    }
}
