package qf;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * File store mirroring the Python backend schema: storage/jobs/{id}.json +
 * storage/videos/{id}.mp4. Tolerant reader: corrupt job files are skipped so
 * one bad write never breaks listing. Both backends can share STORAGE_DIR.
 */
public final class Store {

    private Store() {}

    static Path root;
    static int maxRenders = 2;

    public static void init(String dir, int maxConcurrentRenders) {
        root = Path.of(dir);
        maxRenders = Math.max(1, maxConcurrentRenders);
        try {
            Files.createDirectories(root.resolve("jobs"));
            Files.createDirectories(root.resolve("videos"));
            Files.createDirectories(root.resolve("cards"));
            Files.createDirectories(root.resolve("comps"));
        } catch (IOException e) {
            throw new IllegalStateException("storage not writable: " + dir, e);
        }
    }

    public static String topicHash(String topic) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] d = md.digest(topic.strip().toLowerCase().getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (byte b : d) {
                sb.append(String.format("%02x", b));
            }
            return sb.substring(0, 16);
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }

    public static synchronized Map<String, Object> newJob(String topic) {
        Map<String, Object> job = new LinkedHashMap<>();
        job.put("id", UUID.randomUUID().toString().replace("-", "").substring(0, 12));
        job.put("topic", topic);
        job.put("topic_hash", topicHash(topic));
        job.put("status", "queued");
        job.put("stage", "queued");
        job.put("script", null);
        job.put("video_url", null);
        job.put("error", null);
        job.put("created_at", Instant.now().toString());
        save(job);
        return job;
    }

    public static synchronized void save(Map<String, Object> job) {
        try {
            Files.writeString(jobFile((String) job.get("id")),
                    Json.stringify(job), StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new IllegalStateException("job save failed", e);
        }
    }

    public static synchronized Map<String, Object> get(String id) {
        Path p = jobFile(id);
        if (!Files.exists(p)) {
            return null;
        }
        try {
            return Json.obj(Json.parse(Files.readString(p, StandardCharsets.UTF_8)));
        } catch (Exception e) {
            return null;
        }
    }

    public static synchronized List<Map<String, Object>> list(int limit) {
        List<Map<String, Object>> jobs = new ArrayList<>();
        try (var stream = Files.list(root.resolve("jobs"))) {
            stream.filter(p -> p.toString().endsWith(".json")).forEach(p -> {
                try {
                    Map<String, Object> j = Json.obj(Json.parse(Files.readString(p, StandardCharsets.UTF_8)));
                    if (j != null) {
                        jobs.add(j);
                    }
                } catch (Exception ignored) {
                }
            });
        } catch (IOException ignored) {
        }
        jobs.sort(Comparator.comparing((Map<String, Object> j) -> String.valueOf(j.getOrDefault("created_at", ""))).reversed());
        return jobs.size() > limit ? jobs.subList(0, limit) : jobs;
    }

    /** Idempotency cache: same normalized topic with a ready MP4 still on disk. */
    public static synchronized Map<String, Object> findReady(String topic) {
        String th = topicHash(topic);
        for (Map<String, Object> j : list(1000)) {
            if (th.equals(j.get("topic_hash")) && "ready".equals(j.get("status"))
                    && Files.exists(videoPath((String) j.get("id")))) {
                return j;
            }
        }
        return null;
    }

    static Path jobFile(String id) {
        return root.resolve("jobs").resolve(id + ".json");
    }

    public static Path videoPath(String id) {
        return root.resolve("videos").resolve(id + ".mp4");
    }

    public static Path cardsDir(String id) throws IOException {
        Path d = root.resolve("cards").resolve(id);
        Files.createDirectories(d);
        return d;
    }
}
