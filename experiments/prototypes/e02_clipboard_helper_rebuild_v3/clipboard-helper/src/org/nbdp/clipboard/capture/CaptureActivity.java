package org.nbdp.clipboard.capture;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipDescription;
import android.content.ClipboardManager;
import android.os.Bundle;
import android.os.SystemClock;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import org.json.JSONObject;

/** Disposable foreground lab helper. No network, clipboard service or expected data input. */
public final class CaptureActivity extends Activity implements View.OnClickListener {
    private static final int MAX_BYTES = 65536;
    private String caseId;
    private TextView result;
    private Button clear;
    private Button capture;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        result = new TextView(this);
        result.setText("NBDP disposable clipboard capture: awaiting explicit focused action");
        clear = new Button(this);
        clear.setText("Clear clipboard");
        clear.setOnClickListener(this);
        capture = new Button(this);
        capture.setText("Capture clipboard");
        capture.setOnClickListener(this);
        layout.addView(result);
        layout.addView(clear);
        layout.addView(capture);
        setContentView(layout);
        caseId = getIntent().getStringExtra("caseId");
        if (caseId == null || !caseId.matches("[a-z0-9-]{1,48}")) {
            clear.setEnabled(false);
            capture.setEnabled(false);
            result.setText("REFUSED: fixed plan caseId required");
        }
    }

    @Override public void onClick(View view) {
        try {
            if (!hasWindowFocus()) throw new IllegalStateException("Foreground input focus required");
            ClipboardManager manager = (ClipboardManager) getSystemService(CLIPBOARD_SERVICE);
            File directory = new File(getFilesDir(), "captures");
            if (!directory.isDirectory() && !directory.mkdir()) throw new IllegalStateException("Capture directory unavailable");
            if (view == clear) {
                File marker = new File(directory, caseId + ".clear.json");
                if (marker.exists()) throw new IllegalStateException("Clear evidence already exists");
                manager.setPrimaryClip(ClipData.newPlainText("NBDP_EMPTY_" + caseId, ""));
                JSONObject receipt = base("CLEAR");
                receipt.put("status", "EMPTY_SENTINEL_SET");
                writeExclusive(marker, receipt.toString().getBytes(StandardCharsets.UTF_8));
                result.setText("CLEAR complete for " + caseId);
            } else if (view == capture) {
                if (!new File(directory, caseId + ".clear.json").isFile()) throw new IllegalStateException("Clear this case first");
                ClipData clip = manager.getPrimaryClip();
                if (clip == null || clip.getItemCount() != 1 ||
                    !clip.getDescription().hasMimeType(ClipDescription.MIMETYPE_TEXT_PLAIN)) {
                    throw new IllegalStateException("Exactly one text/plain clipboard item required");
                }
                ClipData.Item item = clip.getItemAt(0);
                if (item.getUri() != null || item.getIntent() != null || item.getText() == null) {
                    throw new IllegalStateException("Text only; URI/Intent/coercion refused");
                }
                String text = item.getText().toString();
                if (text.isEmpty() || text.length() > MAX_BYTES) throw new IllegalStateException("Empty/oversized clipboard");
                for (int i = 0; i < text.length(); i++) {
                    char ch = text.charAt(i);
                    if (Character.isHighSurrogate(ch)) {
                        if (++i >= text.length() || !Character.isLowSurrogate(text.charAt(i))) {
                            throw new IllegalStateException("Unpaired Unicode surrogate");
                        }
                    } else if (Character.isLowSurrogate(ch)) throw new IllegalStateException("Unpaired Unicode surrogate");
                }
                byte[] raw = text.getBytes(StandardCharsets.UTF_8);
                if (raw.length > MAX_BYTES) throw new IllegalStateException("UTF-8 size limit");
                JSONObject receipt = base("CAPTURE");
                receipt.put("status", "CAPTURED");
                receipt.put("mime", "text/plain");
                receipt.put("bytes", raw.length);
                receipt.put("sha256", hex(MessageDigest.getInstance("SHA-256").digest(raw)));
                receipt.put("clipboardItemCount", 1);
                receipt.put("clipboardTimestamp", clip.getDescription().getTimestamp());
                writeExclusive(new File(directory, caseId + ".raw.json"), raw);
                writeExclusive(new File(directory, caseId + ".receipt.json"), receipt.toString().getBytes(StandardCharsets.UTF_8));
                result.setText("CAPTURE complete for " + caseId + ": " + raw.length + " bytes");
            }
        } catch (Exception error) {
            result.setText("REFUSED: " + error.getClass().getSimpleName() + ": " + error.getMessage());
        }
    }

    private JSONObject base(String action) throws Exception {
        JSONObject value = new JSONObject();
        value.put("schema", "e02-clipboard-capture-v1");
        value.put("caseId", caseId);
        value.put("action", action);
        value.put("foregroundFocus", hasWindowFocus());
        value.put("elapsedRealtimeNanos", SystemClock.elapsedRealtimeNanos());
        value.put("wallClockMillis", System.currentTimeMillis());
        return value;
    }

    private static String hex(byte[] bytes) {
        StringBuilder value = new StringBuilder();
        for (byte part : bytes) value.append(String.format(java.util.Locale.ROOT, "%02x", part & 255));
        return value.toString();
    }

    private static void writeExclusive(File file, byte[] raw) throws Exception {
        if (!file.createNewFile()) throw new IllegalStateException("Existing evidence is immutable");
        if (!file.setReadable(false, false) || !file.setWritable(false, false) ||
            !file.setReadable(true, true) || !file.setWritable(true, true)) {
            throw new IllegalStateException("Private owner-only file permissions required");
        }
        try (FileOutputStream stream = new FileOutputStream(file, false)) {
            stream.write(raw);
            stream.flush();
            stream.getFD().sync();
        }
    }
}
