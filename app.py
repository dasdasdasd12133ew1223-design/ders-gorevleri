import os
import sys
from datetime import datetime, timedelta
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk
import pystray

import database
import notifications

# Temel renkler ve Windows'ta net görünen arayüz yazı tipi
PALETTE = {
    "background": "#11151B",
    "sidebar": "#171C24",
    "surface": "#1D242E",
    "surface_hover": "#293341",
    "accent": "#D99A35",
    "accent_hover": "#BD7E20",
    "accent_text": "#FFE0A3",
    "muted": "#A3ADBA",
}
ctk.set_appearance_mode("Dark")  # "Dark" veya "Light"
ctk.set_default_color_theme("blue")
ctk.ThemeManager.theme["CTkFont"]["family"] = "Segoe UI"
ctk.ThemeManager.theme["CTkButton"]["fg_color"] = [
    PALETTE["accent"],
    PALETTE["accent_hover"],
]
ctk.ThemeManager.theme["CTkButton"]["hover_color"] = [
    PALETTE["accent_hover"],
    "#A96E19",
]
ctk.ThemeManager.theme["CTkButton"]["text_color"] = ["#FFFFFF", "#FFFFFF"]
ctk.ThemeManager.theme["CTkCheckBox"]["fg_color"] = [
    PALETTE["accent"],
    PALETTE["accent_hover"],
]
ctk.ThemeManager.theme["CTkCheckBox"]["hover_color"] = [
    PALETTE["accent_hover"],
    "#A96E19",
]
ctk.ThemeManager.theme["CTkSwitch"]["progress_color"] = [
    PALETTE["accent"],
    PALETTE["accent_hover"],
]

class TaskModal(ctk.CTkToplevel):
    """Yeni Görev Ekleme veya Düzenleme Penceresi"""
    def __init__(self, parent, task=None, default_course_id=None, on_save_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.task = task
        self.on_save_callback = on_save_callback
        
        self.title("Görev Düzenle" if task else "Yeni Ders Görevi Ekle")
        self.geometry("520x620")
        self.resizable(False, False)
        
        # Pencereyi öne getir
        self.transient(parent)
        self.grab_set()
        
        self.courses = database.get_all_courses()
        self.course_map = {c["name"]: c["id"] for c in self.courses}
        self.id_to_course_name = {c["id"]: c["name"] for c in self.courses}
        
        self.create_widgets(default_course_id)
        
    def create_widgets(self, default_course_id):
        pad_x = 24
        
        # Başlık
        title_lbl = ctk.CTkLabel(
            self, 
            text="📝 " + ("Görevi Düzenle" if self.task else "Yeni Ders Görevi / Plan"), 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_lbl.pack(anchor="w", padx=pad_x, pady=(20, 10))
        
        # Görev Başlığı
        ctk.CTkLabel(self, text="Görev Başlığı *", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=pad_x, pady=(5, 2))
        self.title_entry = ctk.CTkEntry(self, placeholder_text="Örn: Matematik Türev Testi 3 Çözülecek", height=38, font=ctk.CTkFont(size=14))
        self.title_entry.pack(fill="x", padx=pad_x, pady=(0, 10))
        if self.task:
            self.title_entry.insert(0, self.task["title"])
            
        # Ders Seçimi
        ctk.CTkLabel(self, text="Ders / Kategori", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=pad_x, pady=(5, 2))
        course_names = ["(Ders Seçilmedi)"] + [c["name"] for c in self.courses]
        
        initial_course = "(Ders Seçilmedi)"
        if self.task and self.task["course_id"]:
            initial_course = self.id_to_course_name.get(self.task["course_id"], "(Ders Seçilmedi)")
        elif default_course_id and default_course_id in self.id_to_course_name:
            initial_course = self.id_to_course_name[default_course_id]
            
        self.course_combo = ctk.CTkComboBox(self, values=course_names, height=36, font=ctk.CTkFont(size=13))
        self.course_combo.set(initial_course)
        self.course_combo.pack(fill="x", padx=pad_x, pady=(0, 10))
        
        # Açıklama / Notlar
        ctk.CTkLabel(self, text="Notlar / Detaylar", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=pad_x, pady=(5, 2))
        self.desc_text = ctk.CTkTextbox(self, height=80, font=ctk.CTkFont(size=13))
        self.desc_text.pack(fill="x", padx=pad_x, pady=(0, 10))
        if self.task and self.task["description"]:
            self.desc_text.insert("1.0", self.task["description"])
            
        # Tarih & Hızlı Butonlar
        ctk.CTkLabel(self, text="Son Tarih (YYYY-AA-GG)", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=pad_x, pady=(5, 2))
        
        date_frame = ctk.CTkFrame(self, fg_color="transparent")
        date_frame.pack(fill="x", padx=pad_x, pady=(0, 5))
        
        self.date_entry = ctk.CTkEntry(date_frame, placeholder_text="2026-10-11", height=36)
        self.date_entry.pack(side="left", fill="x", expand=True)
        if self.task and self.task["due_date"]:
            self.date_entry.insert(0, self.task["due_date"])
        else:
            self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
            
        btn_today = ctk.CTkButton(date_frame, text="Bugün", width=65, height=36, fg_color="#334155", hover_color="#475569", command=self.set_today)
        btn_today.pack(side="left", padx=(8, 4))
        
        btn_tomorrow = ctk.CTkButton(date_frame, text="Yarın", width=65, height=36, fg_color="#334155", hover_color="#475569", command=self.set_tomorrow)
        btn_tomorrow.pack(side="left", padx=4)
        
        # Saat ve Öncelik
        time_priority_frame = ctk.CTkFrame(self, fg_color="transparent")
        time_priority_frame.pack(fill="x", padx=pad_x, pady=(5, 10))
        
        # Saat
        time_sub = ctk.CTkFrame(time_priority_frame, fg_color="transparent")
        time_sub.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(time_sub, text="Hatırlatıcı Saati (SS:DD)", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(0, 2))
        self.time_entry = ctk.CTkEntry(time_sub, placeholder_text="Örn: 18:30", height=36)
        self.time_entry.pack(fill="x")
        if self.task and self.task["due_time"]:
            self.time_entry.insert(0, self.task["due_time"])
        else:
            # Şimdiki saatten 1 saat sonrasını varsayılan öner
            default_t = (datetime.now() + timedelta(hours=1)).strftime("%H:00")
            self.time_entry.insert(0, default_t)
            
        # Öncelik
        priority_sub = ctk.CTkFrame(time_priority_frame, fg_color="transparent")
        priority_sub.pack(side="right", fill="x", expand=True)
        ctk.CTkLabel(priority_sub, text="Öncelik Derecesi", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(0, 2))
        self.priority_combo = ctk.CTkComboBox(priority_sub, values=["Düşük", "Normal", "Yüksek"], height=36)
        if self.task and self.task["priority"]:
            self.priority_combo.set(self.task["priority"])
        else:
            self.priority_combo.set("Normal")
        self.priority_combo.pack(fill="x")
        
        # Bilgi Notu
        hint_lbl = ctk.CTkLabel(self, text="💡 Belirlediğiniz tarih ve saatte Windows bildirimi ile uyarılacaksınız.", font=ctk.CTkFont(size=11), text_color="#94A3B8")
        hint_lbl.pack(anchor="w", padx=pad_x, pady=(5, 15))
        
        # Butonlar
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=pad_x, pady=(10, 20))
        
        cancel_btn = ctk.CTkButton(btn_frame, text="İptal", fg_color="#475569", hover_color="#64748B", height=40, command=self.destroy)
        cancel_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        save_btn = ctk.CTkButton(btn_frame, text="Görevi Kaydet", height=40, font=ctk.CTkFont(weight="bold"), command=self.save_task)
        save_btn.pack(side="right", fill="x", expand=True)

    def set_today(self):
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

    def set_tomorrow(self):
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"))

    def save_task(self):
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Eksik Bilgi", "Lütfen görev başlığını giriniz.")
            return
            
        desc = self.desc_text.get("1.0", "end-1c").strip()
        
        course_name = self.course_combo.get()
        course_id = self.course_map.get(course_name, None)
        
        due_date = self.date_entry.get().strip() or None
        due_time = self.time_entry.get().strip() or None
        priority = self.priority_combo.get()
        
        # Basit tarih doğrulaması
        if due_date:
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Hatalı Tarih", "Tarih formatı YYYY-AA-GG olmalıdır (Örn: 2026-10-15).")
                return

        # Basit saat doğrulaması
        if due_time:
            try:
                datetime.strptime(due_time, "%H:%M")
            except ValueError:
                messagebox.showerror("Hatalı Saat", "Saat formatı SS:DD olmalıdır (Örn: 14:30).")
                return

        if self.task:
            database.update_task(self.task["id"], title, desc, course_id, due_date, due_time, priority)
        else:
            database.add_task(title, desc, course_id, due_date, due_time, priority)
            
        if self.on_save_callback:
            self.on_save_callback()
            
        self.destroy()


class AddCourseModal(ctk.CTkToplevel):
    """Yeni Ders Ekleme Penceresi"""
    def __init__(self, parent, on_save_callback=None):
        super().__init__(parent)
        self.on_save_callback = on_save_callback
        
        self.title("Yeni Ders Ekle")
        self.geometry("380x250")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        pad_x = 20
        ctk.CTkLabel(self, text="📚 Yeni Ders Tanımla", font=ctk.CTkFont(size=17, weight="bold")).pack(anchor="w", padx=pad_x, pady=(20, 10))
        
        ctk.CTkLabel(self, text="Ders Adı", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=pad_x, pady=(5, 2))
        self.name_entry = ctk.CTkEntry(self, placeholder_text="Örn: Geometri / Veri Yapıları", height=38)
        self.name_entry.pack(fill="x", padx=pad_x, pady=(0, 15))
        
        # Renk seçimi (popüler renkler)
        self.colors = ["#3B82F6", "#8B5CF6", "#EC4899", "#10B981", "#F59E0B", "#EF4444", "#06B6D4"]
        self.selected_color = self.colors[0]
        
        color_frame = ctk.CTkFrame(self, fg_color="transparent")
        color_frame.pack(fill="x", padx=pad_x, pady=(0, 20))
        
        ctk.CTkLabel(color_frame, text="Renk:").pack(side="left", padx=(0, 10))
        self.color_buttons = []
        for color in self.colors:
            btn = ctk.CTkButton(
                color_frame, 
                text="", 
                width=24, 
                height=24, 
                corner_radius=12,
                fg_color=color, 
                hover_color=color,
                command=lambda c=color: self.select_color(c)
            )
            btn.pack(side="left", padx=3)
            self.color_buttons.append((btn, color))
            
        # Kaydet butonu
        btn_save = ctk.CTkButton(self, text="Dersi Kaydet", height=38, font=ctk.CTkFont(weight="bold"), command=self.save_course)
        btn_save.pack(fill="x", padx=pad_x)
        
    def select_color(self, color):
        self.selected_color = color
        
    def save_course(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Eksik Bilgi", "Lütfen ders adını yazınız.")
            return
            
        res = database.add_course(name, self.selected_color)
        if res is None:
            messagebox.showerror("Hata", "Bu isimde bir ders zaten mevcut!")
            return
            
        if self.on_save_callback:
            self.on_save_callback()
        self.destroy()


class TaskCard(ctk.CTkFrame):
    """Google Görevler Stili Görev Kartı"""
    def __init__(self, parent, task, on_status_change, on_edit, on_delete):
        super().__init__(parent, corner_radius=10, fg_color="#1E293B" if ctk.get_appearance_mode() == "Dark" else "#FFFFFF")
        self.task = task
        self.on_status_change = on_status_change
        self.on_edit = on_edit
        self.on_delete = on_delete
        
        self.create_widgets()
        
    def create_widgets(self):
        is_done = bool(self.task["is_completed"])
        
        # İçerik konteyneri
        main_layout = ctk.CTkFrame(self, fg_color="transparent")
        main_layout.pack(fill="both", expand=True, padx=14, pady=12)
        
        # Sol: Checkbox
        self.check_var = ctk.BooleanVar(value=is_done)
        self.checkbox = ctk.CTkCheckBox(
            main_layout, 
            text="", 
            variable=self.check_var, 
            width=24, 
            checkbox_width=22, 
            checkbox_height=22,
            corner_radius=11, # Yuvarlak Google Tasks hissi
            fg_color="#10B981",
            hover_color="#059669",
            command=self.toggle_check
        )
        self.checkbox.pack(side="left", anchor="n", padx=(0, 12), pady=(3, 0))
        
        # Orta: Görev Bilgileri
        info_frame = ctk.CTkFrame(main_layout, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)
        
        # Başlık
        title_font = ctk.CTkFont(size=15, weight="bold", overstrike=is_done)
        title_color = "#94A3B8" if is_done else ("#F8FAFC" if ctk.get_appearance_mode() == "Dark" else "#0F172A")
        
        title_label = ctk.CTkLabel(info_frame, text=self.task["title"], font=title_font, text_color=title_color, anchor="w")
        title_label.pack(fill="x", anchor="w")
        
        # Açıklama (varsa)
        if self.task["description"]:
            desc_font = ctk.CTkFont(size=12, overstrike=is_done)
            desc_label = ctk.CTkLabel(info_frame, text=self.task["description"], font=desc_font, text_color="#64748B", anchor="w", justify="left")
            desc_label.pack(fill="x", anchor="w", pady=(2, 4))
            
        # Rozetler (Badges) Alanı: Ders, Tarih/Saat, Öncelik
        badge_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        badge_frame.pack(fill="x", anchor="w", pady=(4, 0))
        
        # Ders Rozeti
        if self.task["course_name"]:
            course_color = self.task["course_color"] or "#3B82F6"
            course_badge = ctk.CTkLabel(
                badge_frame,
                text=f"📚 {self.task['course_name']}",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=course_color,
                text_color="#FFFFFF",
                corner_radius=6,
                padx=8,
                pady=2
            )
            course_badge.pack(side="left", padx=(0, 6))
            
        # Tarih Rozeti
        if self.task["due_date"]:
            due_text = self.format_due_date(self.task["due_date"], self.task["due_time"])
            date_bg = "#334155" if not is_done else "#1E293B"
            date_fg = "#E2E8F0"
            
            # Gecikmişse veya bugünse vurgula
            today_str = datetime.now().strftime("%Y-%m-%d")
            if not is_done:
                if self.task["due_date"] < today_str:
                    date_bg = "#EF4444" # Kırmızı gecikmiş
                    date_fg = "#FFFFFF"
                elif self.task["due_date"] == today_str:
                    date_bg = "#F59E0B" # Sarı/Turuncu bugün
                    date_fg = "#FFFFFF"
                    
            date_badge = ctk.CTkLabel(
                badge_frame,
                text=due_text,
                font=ctk.CTkFont(size=11),
                fg_color=date_bg,
                text_color=date_fg,
                corner_radius=6,
                padx=8,
                pady=2
            )
            date_badge.pack(side="left", padx=(0, 6))
            
        # Öncelik Rozeti
        priority = self.task["priority"]
        if priority == "Yüksek":
            p_badge = ctk.CTkLabel(badge_frame, text="⚡ Acil", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#DC2626", text_color="#FFFFFF", corner_radius=6, padx=8, pady=2)
            p_badge.pack(side="left", padx=(0, 6))
        elif priority == "Düşük":
            p_badge = ctk.CTkLabel(badge_frame, text="☕ Düşük", font=ctk.CTkFont(size=11), fg_color="#475569", text_color="#E2E8F0", corner_radius=6, padx=8, pady=2)
            p_badge.pack(side="left", padx=(0, 6))
            
        # Sağ: Aksiyon Butonları (Düzenle & Sil)
        action_frame = ctk.CTkFrame(main_layout, fg_color="transparent")
        action_frame.pack(side="right", anchor="center", padx=(10, 0))
        
        edit_btn = ctk.CTkButton(
            action_frame, 
            text="✏️", 
            width=32, 
            height=32, 
            fg_color="transparent", 
            hover_color="#334155", 
            font=ctk.CTkFont(size=14),
            command=lambda: self.on_edit(self.task)
        )
        edit_btn.pack(side="left", padx=2)
        
        del_btn = ctk.CTkButton(
            action_frame, 
            text="🗑️", 
            width=32, 
            height=32, 
            fg_color="transparent", 
            hover_color="#7F1D1D", 
            font=ctk.CTkFont(size=14),
            command=lambda: self.on_delete(self.task["id"])
        )
        del_btn.pack(side="left", padx=2)

    def format_due_date(self, date_str, time_str):
        today = datetime.now().date()
        try:
            task_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if task_date == today:
                date_repr = "Bugün"
            elif task_date == today + timedelta(days=1):
                date_repr = "Yarın"
            elif task_date == today - timedelta(days=1):
                date_repr = "Dün (Gecikti)"
            else:
                date_repr = task_date.strftime("%d %b")
        except Exception:
            date_repr = date_str
            
        if time_str:
            return f"⏰ {date_repr}, {time_str}"
        return f"📅 {date_repr}"

    def toggle_check(self):
        new_val = self.check_var.get()
        self.on_status_change(self.task["id"], new_val)


class GoogleTasksApp(ctk.CTk):
    """Google Görevler Tarzı Ana Uygulama"""
    def __init__(self):
        super().__init__()

        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.logo_path = os.path.join(self.app_dir, "assets", "logo.png")
        self.logo_ico_path = os.path.join(self.app_dir, "assets", "logo.ico")
        self.member = None
        self.tray_icon = None
        self.login_mode = "login"

        self.title("Ders Görevleri")
        self.geometry("480x620")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.bind("<Unmap>", self.on_minimize)

        self.logo_image = Image.open(self.logo_path).convert("RGBA")
        self.window_icon = ImageTk.PhotoImage(self.logo_image.resize((64, 64), Image.Resampling.LANCZOS))
        self.iconphoto(True, self.window_icon)
        self.iconbitmap(self.logo_ico_path)
        self.tray_icon = pystray.Icon(
            "Ders Görevleri",
            self.logo_image.resize((64, 64), Image.Resampling.LANCZOS),
            "Ders Görevleri",
            menu=pystray.Menu(
                pystray.MenuItem("Uygulamayı aç", self.tray_open, default=True),
                pystray.MenuItem("Çıkış", self.tray_exit),
            ),
        )
        self.tray_icon.run_detached()

        database.init_membership_db()
        remembered_member = database.get_remembered_member()
        if remembered_member:
            self.open_member(remembered_member)
        else:
            self.show_auth_screen()

        if "--tray" in sys.argv:
            self.withdraw()

    def show_auth_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.geometry("480x620")
        self.resizable(False, False)
        panel = ctk.CTkFrame(self, corner_radius=20)
        panel.pack(fill="both", expand=True, padx=28, pady=28)

        logo = Image.open(self.logo_path).convert("RGBA")
        self.auth_logo = ctk.CTkImage(
            light_image=logo,
            dark_image=logo,
            size=(96, 96),
        )
        ctk.CTkLabel(panel, image=self.auth_logo, text="").pack(pady=(24, 8))
        ctk.CTkLabel(
            panel,
            text="Ders Görevleri",
            font=ctk.CTkFont(size=25, weight="bold"),
        ).pack()
        self.auth_heading = ctk.CTkLabel(
            panel,
            text="Hesabınıza giriş yapın",
            text_color="#94A3B8",
        )
        self.auth_heading.pack(pady=(6, 20))

        self.email_entry = ctk.CTkEntry(
            panel, placeholder_text="E-posta", height=42, width=340
        )
        self.email_entry.pack(pady=7)
        self.password_entry = ctk.CTkEntry(
            panel, placeholder_text="Şifre", show="•", height=42, width=340
        )
        self.password_entry.pack(pady=7)
        self.confirm_password_entry = ctk.CTkEntry(
            panel, placeholder_text="Şifreyi tekrar girin", show="•", height=42, width=340
        )

        self.auth_error = ctk.CTkLabel(
            panel, text="", text_color="#F87171", wraplength=340
        )
        self.auth_error.pack(pady=(6, 2))
        self.auth_submit = ctk.CTkButton(
            panel,
            text="Giriş Yap",
            width=340,
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.submit_auth,
        )
        self.auth_submit.pack(pady=(8, 10))
        self.auth_switch = ctk.CTkButton(
            panel,
            text="Hesabın yok mu? Üye ol",
            fg_color="transparent",
            hover_color="#334155",
            command=self.toggle_auth_mode,
        )
        self.auth_switch.pack()
        ctk.CTkLabel(
            panel,
            text="Hesap bu bilgisayarda saklanır. Çevrimiçi üyelik ve ödeme henüz bağlı değildir.",
            font=ctk.CTkFont(size=11),
            text_color="#64748B",
            wraplength=340,
            justify="center",
        ).pack(pady=(16, 18))
        self.password_entry.bind("<Return>", lambda _event: self.submit_auth())
        self.set_auth_mode("login")

    def set_auth_mode(self, mode):
        self.login_mode = mode
        registering = mode == "register"
        self.auth_heading.configure(
            text="Yeni hesabınızı oluşturun" if registering else "Hesabınıza giriş yapın"
        )
        self.auth_submit.configure(text="Üye Ol" if registering else "Giriş Yap")
        self.auth_switch.configure(
            text="Zaten hesabın var mı? Giriş yap"
            if registering
            else "Hesabın yok mu? Üye ol"
        )
        if registering:
            self.confirm_password_entry.pack(pady=7, after=self.password_entry)
        else:
            self.confirm_password_entry.pack_forget()
        self.auth_error.configure(text="")
        self.geometry("480x680" if registering else "480x620")

    def toggle_auth_mode(self):
        self.set_auth_mode("register" if self.login_mode == "login" else "login")

    def submit_auth(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        if not email or "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            self.auth_error.configure(text="Geçerli bir e-posta adresi girin.")
            return
        if len(password) < 8:
            self.auth_error.configure(text="Şifre en az 8 karakter olmalıdır.")
            return

        if self.login_mode == "register":
            if password != self.confirm_password_entry.get():
                self.auth_error.configure(text="Şifreler eşleşmiyor.")
                return
            member = database.create_member(email, password)
            if member is None:
                self.auth_error.configure(
                    text="Bu e-posta ile zaten hesap var. Giriş yapmayı deneyin."
                )
                return
        else:
            member = database.authenticate_member(email, password)
            if member is None:
                self.auth_error.configure(text="E-posta veya şifre hatalı.")
                return

        database.remember_member(member["id"])
        self.open_member(member)

    def open_member(self, member):
        self.member = member
        database.select_member_database(member["id"])
        database.init_db()
        notifications.notifier.start_service()
        for widget in self.winfo_children():
            widget.destroy()
        self.title(f"Ders Görevleri — {member['email']}")
        self.geometry("1060x680")
        self.minsize(860, 560)
        self.resizable(True, True)

        # Seçili filtre ve ders
        self.current_filter = "all"  # all, today, upcoming, completed, course
        self.current_course_id = None
        self.search_term = ""
        self.course_buttons = []
        self.create_layout()
        self.load_courses()
        self.load_tasks()
        self.update_stats()

    def tray_open(self, _icon=None, _item=None):
        self.after(0, self.show_from_tray)

    def show_from_tray(self):
        self.deiconify()
        self.state("normal")
        self.lift()
        self.focus_force()

    def hide_to_tray(self):
        self.withdraw()

    def on_minimize(self, _event=None):
        if self.state() == "iconic":
            self.after_idle(self.withdraw)

    def tray_exit(self, _icon=None, _item=None):
        self.after(0, self.destroy_app)

    def destroy_app(self):
        notifications.notifier.stop_service()
        if self.tray_icon:
            self.tray_icon.stop()
        self.destroy()

    def create_layout(self):
        # 2 Ana Kolon: Sol Menü (Sidebar) + Sağ İçerik
        self.grid_columnconfigure(0, weight=0) # Sabit sidebar
        self.grid_columnconfigure(1, weight=1) # Esnek içerik
        self.grid_rowconfigure(0, weight=1)
        
        # ================= SOL SIDEBAR =================
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=PALETTE["sidebar"] if ctk.get_appearance_mode() == "Dark" else "#F1F5F9")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        # Logo / Başlık
        app_title = ctk.CTkLabel(
            self.sidebar, 
            text="Ders Görevleri",
            image=ctk.CTkImage(
                light_image=self.logo_image,
                dark_image=self.logo_image,
                size=(32, 32),
            ),
            compound="left",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=PALETTE["accent_text"]
        )
        app_title.pack(anchor="w", padx=20, pady=(24, 20))
        
        # Standart Filtre Butonları
        self.filter_btns = {}
        filters_meta = [
            ("all", "📋 Tüm Görevler"),
            ("today", "☀️ Bugün"),
            ("upcoming", "📅 Yaklaşanlar"),
            ("completed", "✅ Tamamlananlar"),
        ]
        
        for key, label in filters_meta:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                font=ctk.CTkFont(size=14, weight="normal"),
                anchor="w",
                height=38,
                fg_color=PALETTE["surface"] if key == "all" else "transparent",
                hover_color=PALETTE["surface_hover"],
                command=lambda k=key: self.set_filter(k)
            )
            btn.pack(fill="x", padx=12, pady=3)
            self.filter_btns[key] = btn

        yks_btn = ctk.CTkButton(
            self.sidebar,
            text="📊 YKS Soru Dağılımı",
            font=ctk.CTkFont(size=14, weight="normal"),
            anchor="w",
            height=38,
            fg_color="transparent",
            hover_color=PALETTE["surface_hover"],
            command=lambda: self.set_filter("yks_pdf"),
        )
        yks_btn.pack(fill="x", padx=12, pady=3)
        self.filter_btns["yks_pdf"] = yks_btn
            
        # Ayrıcı Çizgi
        sep = ctk.CTkFrame(self.sidebar, height=1, fg_color=PALETTE["surface_hover"])
        sep.pack(fill="x", padx=15, pady=15)
        
        # Dersler Başlığı ve Ekle Butonu
        course_header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        course_header.pack(fill="x", padx=14, pady=(0, 6))
        
        ctk.CTkLabel(
            course_header, 
            text="DERSLERİM", 
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94A3B8"
        ).pack(side="left")
        
        add_course_btn = ctk.CTkButton(
            course_header,
            text="+ Ders",
            width=50,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color=PALETTE["accent"],
            hover_color=PALETTE["accent_hover"],
            command=self.open_add_course_modal
        )
        add_course_btn.pack(side="right")
        
        # Dersler Scroll Listesi
        self.course_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.course_scroll.pack(fill="both", expand=True, padx=6, pady=4)
        
        # Alt Kısım: İstatistik & Koyu/Açık Mod
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(fill="x", side="bottom", padx=15, pady=15)
        
        self.stats_lbl = ctk.CTkLabel(bottom_frame, text="Kalan: 0  |  Tamamlanan: 0", font=ctk.CTkFont(size=11), text_color="#94A3B8")
        self.stats_lbl.pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            bottom_frame,
            text=self.member["email"],
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8",
            anchor="w",
        ).pack(fill="x", pady=(0, 4))
        ctk.CTkButton(
            bottom_frame,
            text="Çıkış Yap",
            height=28,
            fg_color="transparent",
            hover_color="#334155",
            anchor="w",
            command=self.logout,
        ).pack(fill="x", pady=(0, 8))
        
        self.theme_switch = ctk.CTkSwitch(bottom_frame, text="Karanlık Mod", command=self.toggle_theme)
        self.theme_switch.pack(anchor="w")
        self.theme_switch.select()

        # ================= SAĞ İÇERİK =================
        self.main_content = ctk.CTkFrame(self, fg_color=PALETTE["background"] if ctk.get_appearance_mode() == "Dark" else "#F8FAFC")
        self.main_content.grid(row=0, column=1, sticky="nsew")
        
        # Üst Araç Çubuğu (Top Bar)
        top_bar = ctk.CTkFrame(self.main_content, fg_color="transparent", height=70)
        top_bar.pack(fill="x", padx=28, pady=(20, 10))
        
        self.section_title = ctk.CTkLabel(
            top_bar, 
            text="Tüm Görevler", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.section_title.pack(side="left", anchor="center")
        
        # Yeni Görev Ekle Butonu
        add_task_btn = ctk.CTkButton(
            top_bar,
            text="➕ Yeni Görev Ekle",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=PALETTE["accent"],
            hover_color=PALETTE["accent_hover"],
            corner_radius=8,
            command=self.open_add_task_modal
        )
        add_task_btn.pack(side="right", padx=(10, 0))
        
        # Canlı Arama Çubuğu
        self.search_entry = ctk.CTkEntry(
            top_bar,
            placeholder_text="🔍 Görev veya not ara...",
            width=240,
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.search_entry.pack(side="right")
        self.search_entry.bind("<KeyRelease>", self.on_search)
        
        # Görev Kartları Listesi (Scrollable)
        self.tasks_container = ctk.CTkScrollableFrame(self.main_content, fg_color="transparent")
        self.tasks_container.pack(fill="both", expand=True, padx=28, pady=(10, 20))
        
    def set_filter(self, filter_name, course_id=None, title_override=None):
        self.current_filter = filter_name
        self.current_course_id = course_id
        
        # Menü vurgularını güncelle
        for k, btn in self.filter_btns.items():
            btn.configure(fg_color=PALETTE["surface"] if k == filter_name else "transparent")
            
        for btn, c_id in self.course_buttons:
            btn.configure(fg_color=PALETTE["surface"] if (filter_name == "course" and c_id == course_id) else "transparent")
            
        if title_override:
            self.section_title.configure(text=title_override)
        elif filter_name == "all":
            self.section_title.configure(text="Tüm Görevler")
        elif filter_name == "today":
            self.section_title.configure(text="Bugünün Görevleri")
        elif filter_name == "upcoming":
            self.section_title.configure(text="Yaklaşan Görevler")
        elif filter_name == "completed":
            self.section_title.configure(text="Tamamlanan Görevler")
        elif filter_name == "yks_pdf":
            self.section_title.configure(text="YKS Soru Dağılımı")
            
        self.load_tasks()

    def load_courses(self):
        # Mevcut ders butonlarını temizle
        for widget in self.course_scroll.winfo_children():
            widget.destroy()
        self.course_buttons.clear()
        
        courses = database.get_all_courses()
        for course in courses:
            c_frame = ctk.CTkFrame(self.course_scroll, fg_color="transparent")
            c_frame.pack(fill="x", pady=2)
            
            # Sol renk çubuğu / ikonu
            c_btn = ctk.CTkButton(
                c_frame,
                text=f"●  {course['name']}",
                font=ctk.CTkFont(size=13),
                anchor="w",
                height=34,
                fg_color="transparent",
                text_color=course["color"],
                hover_color="#334155",
                command=lambda cid=course["id"], cname=course["name"]: self.set_filter("course", cid, f"📚 {cname}")
            )
            c_btn.pack(side="left", fill="x", expand=True)
            self.course_buttons.append((c_btn, course["id"]))
            
            # Ders Silme Butonu (sağdaki ufak çarpı)
            del_c_btn = ctk.CTkButton(
                c_frame,
                text="✕",
                width=24,
                height=24,
                font=ctk.CTkFont(size=10),
                fg_color="transparent",
                text_color="#64748B",
                hover_color="#EF4444",
                command=lambda cid=course["id"], cname=course["name"]: self.confirm_delete_course(cid, cname)
            )
            del_c_btn.pack(side="right", padx=(2, 0))

    def confirm_delete_course(self, course_id, course_name):
        if messagebox.askyesno("Dersi Sil", f"'{course_name}' dersini silmek istediğinize emin misiniz?\n(Görevler silinmez, derssiz duruma geçer)"):
            database.delete_course(course_id)
            self.load_courses()
            if self.current_course_id == course_id:
                self.set_filter("all")
            else:
                self.load_tasks()

    def load_tasks(self):
        for widget in self.tasks_container.winfo_children():
            widget.destroy()

        if self.current_filter == "yks_pdf":
            self.load_yks_distribution()
            return
            
        tasks = database.get_tasks(
            filter_type=self.current_filter,
            course_id=self.current_course_id,
            search_query=self.search_term
        )
        
        if not tasks:
            empty_box = ctk.CTkFrame(self.tasks_container, fg_color="transparent")
            empty_box.pack(expand=True, pady=100)
            
            icon = "🎉" if self.current_filter == "completed" else "✨"
            msg = "Burada henüz bir görev yok!" if not self.search_term else "Aramanızla eşleşen görev bulunamadı."
            
            ctk.CTkLabel(empty_box, text=icon, font=ctk.CTkFont(size=44)).pack()
            ctk.CTkLabel(empty_box, text=msg, font=ctk.CTkFont(size=16, weight="bold"), text_color="#94A3B8").pack(pady=(10, 4))
            ctk.CTkLabel(empty_box, text="Yeni bir ders görevi eklemek için yukarıdaki butonu kullanabilirsiniz.", font=ctk.CTkFont(size=12), text_color="#64748B").pack()
            return
            
        for task in tasks:
            card = TaskCard(
                self.tasks_container,
                task=task,
                on_status_change=self.handle_task_toggle,
                on_edit=self.open_edit_task_modal,
                on_delete=self.handle_task_delete
            )
            card.pack(fill="x", pady=5)

    def load_yks_distribution(self):
        sections = [
            (
                "TYT Matematik & Geometri · 40 soru",
                [
                    ("Problemler", "Sayı-kesir, yaş, yüzde-kâr-zarar, hız, karışım, rutin olmayan ve grafik okuma problemleri.", "12–13"),
                    ("Temel Kavramlar & Sayılar", "Tek-çift, ardışık ve asal sayılar; sayı basamakları ve bölünebilme kuralları.", "4–5"),
                    ("Üslü – Köklü – Mutlak Değer", "Denklemler, basit eşitsizlikler, mutlak değerli ifadeler ve üslü-köklü işlemler.", "3–4"),
                    ("Kümeler, Mantık & Fonksiyonlar", "Alt kümeler ve işlemler, sembolik mantık, fonksiyon grafikleri ve tanım kümesi.", "3–4"),
                    ("PKOB & İstatistik", "Permütasyon, kombinasyon, olasılık; veri analizi, aritmetik ortalama, mod ve medyan.", "2–3"),
                    ("Üçgenler", "Açı-kenar bağıntıları, dik üçgen, Pisagor-Öklid, alan ve benzerlik.", "3–4"),
                    ("Çokgenler & Dörtgenler", "Düzgün çokgenler, paralelkenar, eşkenar dörtgen, yamuk ve kare.", "2–3"),
                    ("Katı Cisimler", "Prizma, piramit, silindir, koni ve kürede alan-hacim hesaplamaları.", "2"),
                    ("Analitik Geometri", "Nokta ve doğru analitiği, eğim ve eksenleri kestiği noktalar.", "1–2"),
                ],
            ),
            (
                "TYT Fen Bilimleri · 20 soru",
                [
                    ("Fizik: Optik & Dalgalar", "Aydınlanma, aynalar, kırılma, mercekler, renkler; yay ve su dalgaları.", "2–3"),
                    ("Fizik: Elektrik & Madde", "Elektrik devreleri ve Ohm kanunu; dayanıklılık, özkütle, kaldırma kuvveti ve basınç.", "2–3"),
                    ("Fizik: Mekanik & Isı", "Vektörler, doğrusal hareket, Newton yasaları, ısı-sıcaklık ve genleşme.", "2"),
                    ("Kimya: Atom & Etkileşimler", "Periyodik sistem, iyonik-kovalent-metalik bağlar ve zayıf etkileşimler.", "2–3"),
                    ("Kimya: Hâller & Mol", "Maddenin hâlleri, mol, tepkime hesaplamaları, karışımlar ve ayırma yöntemleri.", "2–3"),
                    ("Kimya: Asit, Baz & Tuz", "pH, nötralleşme, tuzların kullanım alanları, sabun ve deterjan.", "1–2"),
                    ("Biyoloji: Hücre & Canlılar", "Organeller, madde geçişleri ve sınıflandırma basamakları.", "2"),
                    ("Biyoloji: Kalıtım & Bölünmeler", "Mitoz, mayoz, kalıtım ve soyağacı analizi.", "2"),
                    ("Biyoloji: Ekosistem", "Besin ağı, trofik düzeyler, madde döngüleri ve çevre.", "2"),
                ],
            ),
            (
                "AYT Matematik & Geometri · 40 soru",
                [
                    ("Türev", "Türev kuralları, teğet-normal, artan-azalan aralıklar, ekstremum ve maksimum-minimum problemleri.", "3–4"),
                    ("İntegral", "Belirsiz-belirli integral, Riemann toplamı ve eğri altında/iki eğri arasında kalan alan.", "3–4"),
                    ("Limit & Süreklilik", "Sağdan-soldan limit, belirsizlikler, süreklilik şartı ve grafik okuma.", "2"),
                    ("Trigonometri", "Fonksiyonlar, özdeşlikler, toplam-fark ve iki kat açı formülleri, denklemler.", "4–5"),
                    ("Logaritma & Diziler", "Logaritma özellikleri, taban değiştirme, denklemler-eşitsizlikler, aritmetik ve geometrik diziler.", "3–4"),
                    ("Polinomlar & İkinci Derece", "Bölme-kalan, kök-katsayı ilişkileri, parabol ve eşitsizlik tablosu.", "3–4"),
                    ("Fonksiyonlar & Karmaşık Sayılar", "Bileşke ve ters fonksiyon; karmaşık sayılarda işlemler ve eşlenik.", "2–3"),
                    ("PKOB & Binom", "Seçme-sıralama, bağımsız olasılık ve binom açılımı genel terimi.", "2–3"),
                    ("Analitik Geometri", "Nokta-doğru analitiği, doğrular arası açı ve dönüşüm geometrisi.", "3–4"),
                    ("Çember & Daire", "Açı, teğet-kiriş, çevre, daire dilimi alanı ve çember analitiği.", "2–3"),
                ],
            ),
            (
                "AYT Fen Bilimleri · 40 soru",
                [
                    ("Fizik: Mekanik", "Vektörler, tork-denge, kütle merkezi, basit makineler, atışlar, momentum ve enerji.", "4–5"),
                    ("Fizik: Elektrik & Manyetizma", "Elektriksel alan-potansiyel, kondansatörler, manyetik alan, indüksiyon, alternatif akım ve transformatörler.", "3–4"),
                    ("Fizik: Çembersel Hareket & Dalgalar", "Çembersel hareket, açısal momentum, basit harmonik hareket ve girişim.", "3"),
                    ("Fizik: Modern Fizik", "Görelilik, fotoelektrik olay, Compton saçılması, atom modelleri, X-ışınları ve radyoaktivite.", "3"),
                    ("Kimya: Atom, Gaz & Çözelti", "Kuantum sayıları, elektron dizilimi, ideal gaz, molarite-molalite ve koligatif özellikler.", "3–4"),
                    ("Kimya: Enerji, Hız & Denge", "Tepkime ısısı, tepkime hızı, kimyasal denge, asit-baz dengesi ve çözünürlük dengesi.", "3–4"),
                    ("Kimya: Elektrokimya", "Yükseltgenme basamakları, aktiflik, elektrokimyasal piller, elektroliz ve Faraday kanunları.", "2"),
                    ("Kimya: Organik Kimya", "Hibritleşme, molekül geometrisi, hidrokarbonlar ve temel fonksiyonel gruplar.", "3–4"),
                    ("Biyoloji: İnsan Fizyolojisi", "Sinir, duyu, destek-hareket, sindirim, dolaşım-bağışıklık, solunum ve boşaltım sistemleri.", "5–6"),
                    ("Biyoloji: Genden Proteine", "DNA-RNA, replikasyon, transkripsiyon, translasyon ve protein sentezi.", "2–3"),
                ],
            ),
        ]

        ctk.CTkLabel(
            self.tasks_container,
            text="2018–2026 YKS Sayısal Soru Dağılımı",
            font=ctk.CTkFont(size=23, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(16, 6))
        ctk.CTkLabel(
            self.tasks_container,
            text="PDF’deki konu ve alt konu bilgileri aşağıda uygulama içinde gösteriliyor. 2020–2026 eğilimlerine %70 ağırlık verilmiş yaklaşık ortalama soru aralıklarıdır; sınavdan sınava değişebilir.",
            font=ctk.CTkFont(size=13),
            text_color="#94A3B8",
            wraplength=760,
            justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 14))

        for section_title, topics in sections:
            section = ctk.CTkFrame(self.tasks_container, corner_radius=12)
            section.pack(fill="x", padx=12, pady=8)
            section.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                section,
                text=section_title,
                font=ctk.CTkFont(size=17, weight="bold"),
                anchor="w",
            ).grid(row=0, column=0, columnspan=3, sticky="ew", padx=16, pady=(14, 10))

            for row_index, (topic, details, average) in enumerate(topics, start=1):
                row_bg = "#172033" if row_index % 2 else "transparent"
                row = ctk.CTkFrame(section, fg_color=row_bg, corner_radius=6)
                row.grid(row=row_index, column=0, columnspan=3, sticky="ew", padx=10, pady=2)
                row.grid_columnconfigure(1, weight=1)

                ctk.CTkLabel(
                    row,
                    text=topic,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    anchor="w",
                    justify="left",
                    wraplength=190,
                ).grid(row=0, column=0, sticky="nw", padx=(10, 8), pady=8)
                ctk.CTkLabel(
                    row,
                    text=details,
                    font=ctk.CTkFont(size=12),
                    anchor="w",
                    justify="left",
                    wraplength=430,
                ).grid(row=0, column=1, sticky="new", padx=8, pady=8)
                ctk.CTkLabel(
                    row,
                    text=f"{average} soru",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=PALETTE["accent_text"],
                    anchor="e",
                    width=78,
                ).grid(row=0, column=2, sticky="ne", padx=(8, 10), pady=8)

            ctk.CTkFrame(section, height=8, fg_color="transparent").grid(
                row=len(topics) + 1, column=0
            )

    def handle_task_toggle(self, task_id, is_completed):
        database.toggle_task_status(task_id, is_completed)
        self.load_tasks()
        self.update_stats()

    def handle_task_delete(self, task_id):
        database.delete_task(task_id)
        self.load_tasks()
        self.update_stats()

    def open_add_task_modal(self):
        TaskModal(
            self, 
            default_course_id=self.current_course_id, 
            on_save_callback=self.refresh_all
        )

    def open_edit_task_modal(self, task):
        TaskModal(
            self, 
            task=task, 
            on_save_callback=self.refresh_all
        )

    def open_add_course_modal(self):
        AddCourseModal(self, on_save_callback=self.load_courses)

    def refresh_all(self):
        self.load_tasks()
        self.update_stats()

    def update_stats(self):
        stats = database.get_stats()
        self.stats_lbl.configure(text=f"Kalan: {stats['pending']}  |  Tamamlanan: {stats['completed']}")

    def on_search(self, event=None):
        self.search_term = self.search_entry.get().strip()
        self.load_tasks()

    def toggle_theme(self):
        if self.theme_switch.get():
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")
        self.load_tasks()

    def logout(self):
        notifications.notifier.stop_service()
        database.forget_member()
        self.member = None
        self.show_auth_screen()

    def on_closing(self):
        self.hide_to_tray()

if __name__ == "__main__":
    app = GoogleTasksApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
