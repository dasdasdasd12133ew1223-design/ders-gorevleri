import threading
import time
import winsound
from datetime import datetime
import database

try:
    from winotify import Notification, audio
    HAS_WINOTIFY = True
except ImportError:
    HAS_WINOTIFY = False

class NotificationManager:
    def __init__(self):
        self.running = False
        self.thread = None

    def send_notification(self, title, message, course_name=None):
        header = f"📚 {course_name} - Ders Hatırlatması" if course_name else "⏰ Ders / Görev Hatırlatması"
        
        # Ses çal
        try:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass

        # Windows Bildirimi (Toast)
        if HAS_WINOTIFY:
            try:
                toast = Notification(
                    app_id="Ders Görevleri & Hatırlatıcı",
                    title=f"{header}: {title}",
                    msg=message if message else "Bu görevin süresi geldi veya yaklaşıyor!",
                    duration="long"
                )
                toast.set_audio(audio.Reminder, loop=False)
                toast.show()
                return
            except Exception as e:
                print(f"Winotify hatası: {e}")

        print(f"[BİLDİRİM] {header} -> {title}: {message}")

    def _worker(self):
        while self.running:
            try:
                due_tasks = database.get_due_reminders()
                for task in due_tasks:
                    title = task["title"]
                    desc = task["description"] or ""
                    course = task["course_name"]
                    due_date = task["due_date"]
                    due_time = task["due_time"] or ""
                    
                    msg_body = f"Tarih: {due_date} {due_time}\n{desc}".strip()
                    self.send_notification(title, msg_body, course)
                    database.mark_as_reminded(task["id"])
            except Exception as e:
                print(f"Hatırlatıcı döngüsü hatası: {e}")
                
            # Her 20 saniyede bir kontrol et
            time.sleep(20)

    def start_service(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._worker, daemon=True)
            self.thread.start()

    def stop_service(self):
        self.running = False

# Tekil örnek
notifier = NotificationManager()
