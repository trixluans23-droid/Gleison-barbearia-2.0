from pathlib import Path

java_dir = Path("GleisonBarbeariaAndroid/app/src/main/java/com/gleisonbarbearia/app")
main = java_dir / "MainActivity.java"
src = main.read_text(encoding="utf-8")
if "JavascriptInterface" not in src:
    src = src.replace("import android.webkit.WebViewClient;", "import android.webkit.WebViewClient;\nimport android.webkit.JavascriptInterface")
if "GleisonAndroidBridge" not in src:
    src = src.replace("setContentView(webView);", 'webView.addJavascriptInterface(new GleisonAndroidBridge(this), "GleisonAndroid");\n                  setContentView(webView);')
main.write_text(src, encoding="utf-8")

(java_dir / "GleisonAndroidBridge.java").write_text("""package com.gleisonbarbearia.app;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.webkit.JavascriptInterface;

public class GleisonAndroidBridge {
    private final Context context;
    public GleisonAndroidBridge(Context context) { this.context = context.getApplicationContext(); }

    @JavascriptInterface
    public void agendarLembrete(String dataHoraIso, String titulo, String corpo) {
        try {
            String iso = dataHoraIso == null ? "" : dataHoraIso.trim();
            if (iso.length() < 16) return;
            String normalized = iso.replace("T", " ");
            java.text.SimpleDateFormat f = new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss", java.util.Locale.US);
            f.setTimeZone(java.util.TimeZone.getTimeZone("America/Sao_Paulo"));
            java.util.Date d = f.parse(normalized.length() >= 19 ? normalized.substring(0,19) : normalized + ":00");
            if (d == null) return;
            long trigger = d.getTime() - 20L * 60L * 1000L;
            if (trigger <= System.currentTimeMillis()) return;
            Intent intent = new Intent(context, GleisonReminderReceiver.class);
            intent.putExtra("titulo", titulo == null ? "Gleison Barbearia" : titulo);
            intent.putExtra("corpo", corpo == null ? "Seu horário é em aproximadamente 20 minutos." : corpo);
            int requestCode = Math.abs((iso + (titulo == null ? "" : titulo)).hashCode());
            PendingIntent pi = PendingIntent.getBroadcast(context, requestCode, intent, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            AlarmManager am = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
            if (am != null) {
                if (android.os.Build.VERSION.SDK_INT >= 23) am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, trigger, pi);
                else am.setExact(AlarmManager.RTC_WAKEUP, trigger, pi);
            }
        } catch (Exception ignored) {}
    }
}
""", encoding="utf-8")

(java_dir / "GleisonReminderReceiver.java").write_text("""package com.gleisonbarbearia.app;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.media.AudioAttributes;
import android.net.Uri;
import android.os.Build;

public class GleisonReminderReceiver extends BroadcastReceiver {
    private static final String CHANNEL_ID = "gleison_lembrete_v3";

    @Override public void onReceive(Context context, Intent received) {
        NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        Uri sound = Uri.parse("android.resource://" + context.getPackageName() + "/" + R.raw.gleison_notificacao);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(CHANNEL_ID, "Lembretes Gleison Barbearia", NotificationManager.IMPORTANCE_HIGH);
            AudioAttributes aa = new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ALARM).setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build();
            channel.setSound(sound, aa);
            channel.enableVibration(true);
            channel.setVibrationPattern(new long[]{0,180,70,180,70,700});
            manager.createNotificationChannel(channel);
        }
        Intent open = new Intent(context, MainActivity.class);
        open.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent pi = PendingIntent.getActivity(context, 0, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        String titulo = received.getStringExtra("titulo");
        String corpo = received.getStringExtra("corpo");
        if (titulo == null || titulo.trim().isEmpty()) titulo = "Gleison Barbearia";
        if (corpo == null || corpo.trim().isEmpty()) corpo = "Seu horário é em aproximadamente 20 minutos.";
        android.app.Notification.Builder b = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O ? new android.app.Notification.Builder(context, CHANNEL_ID) : new android.app.Notification.Builder(context);
        b.setSmallIcon(R.drawable.ic_stat_notification).setContentTitle(titulo).setContentText(corpo).setStyle(new android.app.Notification.BigTextStyle().bigText(corpo)).setAutoCancel(true).setContentIntent(pi).setPriority(android.app.Notification.PRIORITY_HIGH).setVisibility(android.app.Notification.VISIBILITY_PUBLIC).setVibrate(new long[]{0,180,70,180,70,700});
        manager.notify((int)(System.currentTimeMillis() & 0x7fffffff), b.build());
    }
}
""", encoding="utf-8")

manifest = Path("GleisonBarbeariaAndroid/app/src/main/AndroidManifest.xml")
ms = manifest.read_text(encoding="utf-8")
if "android.permission.SCHEDULE_EXACT_ALARM" not in ms:
    ms = ms.replace('<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />', '<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />\n    <uses-permission android:name="android.permission.SCHEDULE_EXACT_ALARM" />')
if 'android:name=".GleisonReminderReceiver"' not in ms:
    ms = ms.replace("    </application>", '        <receiver android:name=".GleisonReminderReceiver" android:exported="false" />\n    </application>')
manifest.write_text(ms, encoding="utf-8")

html = Path("GleisonBarbeariaAndroid/app/src/main/assets/index.html")
h = html.read_text(encoding="utf-8")
if "GleisonAndroid.agendarLembrete" not in h:
    old = "    localStorage.setItem('gleison_telefone', telefoneNumeros);\n    closeBooking();"
    new = "    localStorage.setItem('gleison_telefone', telefoneNumeros);\n    if(window.GleisonAndroid && typeof window.GleisonAndroid.agendarLembrete==='function'){\n      window.GleisonAndroid.agendarLembrete(dataHora, 'Gleison Barbearia', 'Seu horário é em aproximadamente 20 minutos, às '+selectedTime+' — '+servico+'.');\n    }\n    closeBooking();"
    if old not in h:
        raise SystemExit("Ponto de confirmação do agendamento não encontrado.")
    h = h.replace(old, new, 1)
html.write_text(h, encoding="utf-8")
print("Integração nativa concluída.")
