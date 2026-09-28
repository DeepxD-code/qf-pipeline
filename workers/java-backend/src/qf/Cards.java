package qf;

import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import javax.imageio.ImageIO;

/**
 * Cinematic 1080x1920 cards: glow orb + floating UI panel + captions.
 * Mirrors packages/qf_visuals cards.py (same layout contract).
 */
public final class Cards {

    static final int W = 1080;
    static final int H = 1920;

    private Cards() {}

    static Font font(int size, boolean bold) {
        return new Font(Font.SANS_SERIF, bold ? Font.BOLD : Font.PLAIN, size);
    }

    @SuppressWarnings("unchecked")
    public static List<String> render(Map<String, Object> script, Path outDir, double spi) throws IOException {
        List<Object> scenes = (List<Object>) script.get("scenes");
        String[] widgets = {"player", "stats", "cta"};
        List<String> paths = new ArrayList<>();
        for (int i = 0; i < scenes.size(); i++) {
            Map<String, Object> s = (Map<String, Object>) scenes.get(i);
            BufferedImage img = new BufferedImage(W, H, BufferedImage.TYPE_INT_RGB);
            Graphics2D g = img.createGraphics();
            try {
                g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
                g.setColor(new Color(11, 11, 18));
                g.fillRect(0, 0, W, H);
                glow(g, W / 2, 1250, 750, 460);
                g.setColor(Color.WHITE);
                g.fillRoundRect(60, 90, 340, 80, 24, 24);
                g.setColor(new Color(20, 20, 30));
                g.setFont(font(40, true));
                g.drawString("QONEQT  " + (i + 1) + "/" + scenes.size(), 90, 143);

                g.setFont(font(104, true));
                java.util.List<String> cap = wrap(g, String.valueOf(s.get("caption")), W - 160);
                int y = 260 + 104;
                for (int k = 0; k < Math.min(3, cap.size()); k++) {
                    boolean last = k == Math.min(3, cap.size()) - 1 && cap.size() > 1;
                    g.setColor(last ? new Color(150, 150, 165) : Color.WHITE);
                    g.drawString(cap.get(k), 80, y);
                    y += 132;
                }

                int px = 110, py = 760, pw = W - 220, ph = 560;
                g.setColor(new Color(21, 21, 31));
                g.fillRoundRect(px, py, pw, ph, 36, 36);
                g.setColor(new Color(42, 42, 58));
                g.setStroke(new BasicStroke(3));
                g.drawRoundRect(px, py, pw, ph, 36, 36);

                String kind = widgets[i % widgets.length];
                if (kind.equals("player")) {
                    g.setColor(Color.WHITE);
                    g.setFont(font(38, true));
                    g.drawString(String.valueOf(s.get("title")).toUpperCase(), px + 50, py + 44 + 38);
                    g.setColor(new Color(255, 235, 120));
                    g.setFont(font(30, false));
                    String vo = String.valueOf(s.get("voiceover"));
                    g.drawString(vo.substring(0, Math.min(64, vo.length())), px + 50, py + 110 + 30);
                    progress(g, px + 50, py + 200, pw - 100, 0.35 + 0.2 * i);
                    g.setColor(new Color(160, 160, 175));
                    g.setFont(font(28, false));
                    g.drawString("0:47", px + 50, py + 240 + 28);
                    g.drawString("2:30", px + pw - 140, py + 240 + 28);
                    g.setColor(new Color(255, 235, 120));
                    g.fillOval(px + pw / 2 - 55, py + 320, 110, 110);
                    g.setColor(new Color(20, 20, 30));
                    g.fillPolygon(new int[]{px + pw / 2 - 18, px + pw / 2 - 18, px + pw / 2 + 28},
                            new int[]{py + 345, py + 405, py + 375}, 3);
                } else if (kind.equals("stats")) {
                    g.setColor(Color.WHITE);
                    g.setFont(font(38, true));
                    g.drawString(String.valueOf(s.get("title")).toUpperCase(), px + 50, py + 44 + 38);
                    int by = bars(g, px + 50, py + 130, pw - 100,
                            new String[]{"HOOK RATE", "WATCH TIME"},
                            new double[]{0.43 + 0.1 * i, 0.52 + 0.08 * i});
                    g.setColor(new Color(160, 160, 175));
                    g.setFont(font(30, false));
                    g.drawString("Qoneqt Global Feed", px + 50, by + 90);
                } else {
                    g.setColor(Color.WHITE);
                    g.setFont(font(40, true));
                    g.drawString(String.valueOf(s.get("title")).toUpperCase(), px + 50, py + 60 + 40);
                    g.setColor(new Color(255, 235, 120));
                    g.fillRoundRect(px + 50, py + 380, pw - 100, 100, 50, 50);
                    g.setColor(new Color(20, 20, 30));
                    g.setFont(font(40, true));
                    g.drawString("Post it on Qoneqt", px + 110, py + 408 + 40);
                }
                g.setColor(new Color(200, 200, 210));
                g.setFont(font(36, false));
                g.drawString("Qoneqt Global Feed  9:16", 80, H - 160 + 36);
            } finally {
                g.dispose();
            }
            Path p = outDir.resolve(String.format("scene_%02d.png", i + 1));
            ImageIO.write(img, "png", p.toFile());
            paths.add(p.toString());
        }
        return paths;
    }

    static void glow(Graphics2D g, int cx, int cy, int rx, int ry) {
        int steps = 40;
        for (int i = steps; i >= 1; i--) {
            float f = (float) i / steps;
            int alpha = (int) (110 * (1 - f) * (1 - f));
            g.setColor(new Color(40, 90, 220, Math.max(0, Math.min(255, alpha))));
            g.fillOval((int) (cx - rx * f), (int) (cy - ry * f), (int) (2 * rx * f), (int) (2 * ry * f));
        }
    }

    static void progress(Graphics2D g, int x, int y, int w, double frac) {
        g.setColor(new Color(50, 50, 66));
        g.fillRoundRect(x, y, w, 14, 7, 7);
        g.setColor(new Color(255, 235, 120));
        g.fillRoundRect(x, y, (int) (w * frac), 14, 7, 7);
    }

    static int bars(Graphics2D g, int x, int y, int w, String[] labels, double[] fracs) {
        for (int k = 0; k < labels.length; k++) {
            g.setColor(new Color(200, 200, 210));
            g.setFont(font(30, false));
            g.drawString(labels[k], x, y + 30);
            y += 44;
            g.setColor(new Color(50, 50, 66));
            g.fillRoundRect(x, y, w, 22, 11, 11);
            g.setColor(new Color(120, 220, 140));
            g.fillRoundRect(x, y, (int) (w * fracs[k]), 22, 11, 11);
            y += 58;
        }
        return y;
    }

    static List<String> wrap(Graphics2D g, String text, int maxW) {
        FontMetrics fm = g.getFontMetrics();
        List<String> lines = new ArrayList<>();
        String cur = "";
        for (String w : text.split("\\s+")) {
            String trial = cur.isEmpty() ? w : cur + " " + w;
            if (fm.stringWidth(trial) <= maxW) {
                cur = trial;
            } else {
                if (!cur.isEmpty()) {
                    lines.add(cur);
                }
                cur = w;
            }
        }
        if (!cur.isEmpty()) {
            lines.add(cur);
        }
        return lines;
    }
}
