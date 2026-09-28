package qf;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Topic -&gt; hook + 3-scene plan. Provider chain: OpenAI -&gt; Groq -&gt;
 * deterministic template. Never throws on LLM failure; the pipeline must
 * demo on stage Wi-Fi with expired keys and still produce a valid MP4.
 */
public final class Script {

    private Script() {}

    public static Map<String, Object> generate(String topic) {
        Map<String, Object> s = tryOpenAI(topic);
        if (s != null) {
            return s;
        }
        s = tryGroq(topic);
        return s != null ? s : template(topic);
    }

    public static Map<String, Object> template(String topic) {
        String t = topic.strip().isEmpty() ? "Untitled community story" : topic.strip();
        String punch = punch(t);
        Map<String, Object> s = new LinkedHashMap<>();
        s.put("topic", t);
        s.put("hook", t + " — in 8 seconds, here's why it matters.");
        List<Object> scenes = new ArrayList<>();
        scenes.add(scene("The Hook",
                "Everyone scrolls past " + t + ". Here's the one thing worth stopping for.",
                "STOP SCROLLING", t + ", dramatic cinematic still, hook moment"));
        scenes.add(scene("The Story",
                "Communities on Qoneqt are talking about " + t + " — three takes, one thread.",
                punch, t + ", vivid scene with people, photorealistic"));
        scenes.add(scene("The CTA", "Join the thread on Qoneqt. Post your take and tag it.",
                "POST IT ON QONEQT", "celebration, " + t + ", confetti energy, cinematic"));
        s.put("scenes", scenes);
        s.put("hashtags", List.of("#Qoneqt", "#CtrlFreak"));
        return s;
    }

    static String punch(String topic) {
        java.util.Set<String> filler = java.util.Set.of("through", "the", "a", "an", "in", "on", "of", "and", "to");
        String[] words = topic.strip().split("\\s+");
        StringBuilder sb = new StringBuilder();
        int n = 0;
        for (String w : words) {
            if (n >= 4) {
                break;
            }
            if (filler.contains(w.toLowerCase())) {
                continue;
            }
            if (sb.length() > 0) {
                sb.append(' ');
            }
            sb.append(w.toUpperCase());
            n++;
        }
        return sb.length() == 0 ? "QONEQT" : sb.toString();
    }

    private static Map<String, Object> scene(String title, String voiceover, String caption, String visual) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("title", title);
        m.put("voiceover", voiceover);
        m.put("caption", caption);
        m.put("visual_prompt", visual);
        m.put("duration_s", 2.5);
        return m;
    }

    private static Map<String, Object> tryOpenAI(String topic) {
        String key = System.getenv().getOrDefault("OPENAI_API_KEY", "").strip();
        if (key.isEmpty()) {
            return null;
        }
        String model = System.getenv().getOrDefault("OPENAI_MODEL", "gpt-4o-mini");
        return tryChat("https://api.openai.com/v1/chat/completions", key, model, topic);
    }

    private static Map<String, Object> tryGroq(String topic) {
        String key = System.getenv().getOrDefault("GROQ_API_KEY", "").strip();
        if (key.isEmpty()) {
            return null;
        }
        String model = System.getenv().getOrDefault("GROQ_MODEL", "llama-3.3-70b-versatile");
        return tryChat("https://api.groq.com/openai/v1/chat/completions", key, model, topic);
    }

    private static Map<String, Object> tryChat(String url, String key, String model, String topic) {
        try {
            String prompt = "You write short vertical-video scripts for the Qoneqt Global Feed. "
                    + "Topic: " + topic + ". Return JSON with hook, 3 scenes, hashtags. "
                    + "Keep voiceover under 25 words per scene. No markdown, JSON only.";
            Map<String, Object> body = new LinkedHashMap<>();
            body.put("model", model);
            body.put("temperature", 0.7);
            body.put("messages", List.of(Map.of("role", "user", "content", prompt)));
            HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(30)).build();
            HttpRequest req = HttpRequest.newBuilder(URI.create(url))
                    .timeout(Duration.ofSeconds(30))
                    .header("Authorization", "Bearer " + key)
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(Json.stringify(body)))
                    .build();
            HttpResponse<String> res = client.send(req, HttpResponse.BodyHandlers.ofString());
            if (res.statusCode() < 200 || res.statusCode() >= 300) {
                return null;
            }
            Map<String, Object> data = Json.obj(Json.parse(res.body()));
            if (data == null) {
                return null;
            }
            List<Object> choices = Json.arr(data.get("choices"));
            if (choices == null || choices.isEmpty()) {
                return null;
            }
            Map<String, Object> msg = Json.obj(Json.obj(choices.get(0)).get("message"));
            String text = msg == null ? null : Json.str(msg.get("content"));
            if (text == null) {
                return null;
            }
            String inner = text.substring(text.indexOf('{'), text.lastIndexOf('}') + 1);
            Map<String, Object> d = Json.obj(Json.parse(inner));
            List<Object> scenes = d == null ? null : Json.arr(d.get("scenes"));
            if (scenes == null || scenes.size() < 3) {
                return null;
            }
            List<Object> norm = new ArrayList<>();
            for (int i = 0; i < 3; i++) {
                Map<String, Object> s = Json.obj(scenes.get(i));
                if (s == null) {
                    return null;
                }
                Map<String, Object> m = new LinkedHashMap<>();
                m.put("title", String.valueOf(s.getOrDefault("title", "Scene " + (i + 1))));
                m.put("voiceover", String.valueOf(s.getOrDefault("voiceover", "")));
                m.put("caption", String.valueOf(s.getOrDefault("caption", "")));
                m.put("visual_prompt", String.valueOf(s.getOrDefault("visual_prompt", "")));
                m.put("duration_s", 2.5);
                norm.add(m);
            }
            Map<String, Object> out = new LinkedHashMap<>();
            out.put("topic", topic);
            out.put("hook", String.valueOf(d.getOrDefault("hook", "")));
            out.put("scenes", norm);
            List<Object> tags = Json.arr(d.get("hashtags"));
            out.put("hashtags", tags != null ? tags : List.of());
            return out;
        } catch (Exception e) {
            return null;
        }
    }
}
