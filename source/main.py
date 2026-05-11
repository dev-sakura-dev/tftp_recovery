#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import json
import threading
import socket
import subprocess
import sys
import struct
from urllib.request import urlopen, Request

BG_COLOR = "#0f0f1a"
CARD_BG = "#1a1a2e"
INPUT_BG = "#16213e"
ACCENT = "#7c3aed"
ACCENT_HOVER = "#6d28d9"
ACCENT_LIGHT = "#a78bfa"
RED = "#ef4444"
GREEN = "#10b981"
ORANGE = "#f59e0b"
TEXT_PRIMARY = "#f1f5f9"
TEXT_SECONDARY = "#94a3b8"
SUCCESS = "#10b981"
WARNING = "#f59e0b"
ERROR = "#ef4444"
BORDER = "#334155"

ICONS = {
    "folder": "📂 ",
    "start": "▶ ",
    "stop": "⏹ ",
    "wizard": "🧙 ",
    "settings": "⚙ ",
    "update": "🔄 ",
    "auto": "🔍 ",
    "lang_ru": "🇷🇺",
    "lang_en": "🇬🇧",
    "network": "🌐 ",
    "ip": "📍 ",
    "router": "📡 ",
    "progress": "📊 ",
    "log": "📋 ",
    "error": "❌ ",
    "warning": "⚠ ",
    "info": "ℹ ",
    "success": "✅ ",
    "windows": "🪟 ",
    "linux": "🐧 ",
    "auto_os": "🤖 ",
    "custom": "🔧 ",
    "save": "💾 ",
    "cancel": "🚫 ",
}

LANGUAGES = {
    "ru": {
        "title": "Восстановление роутера",
        "select_folder": "Выбрать папку с прошивкой",
        "start": "▶ Запустить сервер",
        "stop": "⏹ Остановить сервер",
        "settings": "⚙ Настройки",
        "network_interface": "🌐 Сетевой интерфейс",
        "static_ip": "📍 Статический IP",
        "model_select": "📡 Модель роутера",
        "log": "📋 Лог событий",
        "error_line": "❌ Последняя ошибка: ",
        "no_error": "✅ Нет ошибок",
        "update": "🔄 Проверить обновления",
        "lang_toggle": "🇬🇧 English",
        "auto_detect": "🔍 Авто",
        "wizard": "🧙 Мастер восстановления",
        "progress": "📊 Прогресс: ",
        "warning": "⚠ Предупреждение",
        "error": "❌ Ошибка",
        "info": "ℹ Информация",
        "select_folder_error": "Выберите папку с прошивкой",
        "recovery_not_found": "Файл recovery.bin не найден",
        "no_interface": "Не выбран сетевой интерфейс",
        "server_started": "✅ Сервер запущен на порту {port}, ожидание...",
        "server_stopped": "⏹ Сервер остановлен, сеть восстановлена.",
        "os_mode": "💻 Режим ОС",
        "custom_settings": "🔧 Кастомные настройки",
        "custom_ip": "📍 IP адрес",
        "custom_port": "🔌 Порт",
        "custom_file": "📄 Имя файла",
        "save_custom": "💾 Сохранить",
        "cancel": "🚫 Отмена",
        "custom_saved": "✅ Настройки сохранены",
        "ready": "✅ Готов к работе"
    },
    "en": {
        "title": "Router Recovery",
        "select_folder": "Select folder with recovery.bin",
        "start": "▶ Start Server",
        "stop": "⏹ Stop Server",
        "settings": "⚙ Settings",
        "network_interface": "🌐 Network Interface",
        "static_ip": "📍 Static IP",
        "model_select": "📡 Router Model",
        "log": "📋 Event Log",
        "error_line": "❌ Last error: ",
        "no_error": "✅ No errors",
        "update": "🔄 Check for updates",
        "lang_toggle": "🇷🇺 Русский",
        "auto_detect": "🔍 Auto",
        "wizard": "🧙 Recovery Wizard",
        "progress": "📊 Progress: ",
        "warning": "⚠ Warning",
        "error": "❌ Error",
        "info": "ℹ Information",
        "select_folder_error": "Please select firmware folder",
        "recovery_not_found": "recovery.bin not found",
        "no_interface": "No network interface selected",
        "server_started": "✅ Server started on port {port}, waiting...",
        "server_stopped": "⏹ Server stopped, network restored.",
        "os_mode": "💻 OS Mode",
        "custom_settings": "🔧 Custom Settings",
        "custom_ip": "📍 IP Address",
        "custom_port": "🔌 Port",
        "custom_file": "📄 File Name",
        "save_custom": "💾 Save",
        "cancel": "🚫 Cancel",
        "custom_saved": "✅ Settings saved",
        "ready": "✅ Ready to work"
    }
}

WIZARD_STEPS = {
    "ru": [
        ("🔌 Шаг 1: Подключение кабеля", "Подключите Ethernet-кабель к LAN-порту роутера."),
        ("🔋 Шаг 2: Питание", "Отключите питание роутера. Зажмите кнопку Reset."),
        ("⚡ Шаг 3: Включение", "Включите питание, удерживая Reset 10 секунд."),
        ("⏳ Шаг 4: Ожидание", "Сервер ждёт запрос. LAN-индикатор должен мигать."),
        ("✅ Шаг 5: Готово", "Прошивка загружена. Роутер перезагрузится."),
    ],
    "en": [
        ("🔌 Step 1: Connect", "Connect Ethernet cable to router LAN port."),
        ("🔋 Step 2: Power Off", "Power off router. Hold Reset button."),
        ("⚡ Step 3: Power On", "Power on while holding Reset for 10 sec."),
        ("⏳ Step 4: Wait", "Waiting for router request. LAN LED blinks."),
        ("✅ Step 5: Done", "Firmware uploaded. Router will reboot."),
    ]
}

class PureTftpServer:
    def __init__(self, root_dir, port=69):
        self.root_dir = root_dir
        self.port = port
        self.server_socket = None
        self.running = False
        self.log = []
        self.transfer_progress = 0

    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server_socket.bind(('0.0.0.0', self.port))
        except Exception as e:
            self.log.append(f"[ERROR] Port {self.port}: {e}")
            self.running = False
            return
        self.log.append(f"[INFO] TFTP server started on port {self.port}")
        threading.Thread(target=self._listen, daemon=True).start()

    def _listen(self):
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                data, client_addr = self.server_socket.recvfrom(516)
                if data:
                    self._handle_request(data, client_addr)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.log.append(f"[ERROR] {e}")

    def _handle_request(self, data, client_addr):
        try:
            opcode = struct.unpack('!H', data[:2])[0]
            if opcode == 1:
                parts = data[2:].split(b'\x00')
                if len(parts) < 2:
                    raise ValueError("Invalid RRQ")
                filename, mode = parts[0], parts[1].lower()
                if mode not in (b'octet', b'netascii'):
                    self._send_error(client_addr, 0, "Unsupported mode")
                    return
                filepath = os.path.join(self.root_dir, filename.decode())
                if not os.path.isfile(filepath):
                    self._send_error(client_addr, 1, "File not found")
                    return
                self.log.append(f"[INFO] Request: {filename.decode()} from {client_addr}")
                self._send_file(client_addr, filepath)
            else:
                self._send_error(client_addr, 4, "Operation not supported")
        except Exception as e:
            self.log.append(f"[ERROR] Handle: {e}")

    def _send_error(self, client_addr, code, msg):
        packet = struct.pack('!HH', 5, code) + msg.encode() + b'\x00'
        self.server_socket.sendto(packet, client_addr)

    def _send_file(self, client_addr, filepath):
        total_size = os.path.getsize(filepath)
        block_size = 512
        self.transfer_progress = 0
        with open(filepath, 'rb') as f:
            block_num = 1
            while self.running:
                chunk = f.read(block_size)
                if not chunk:
                    break
                packet = struct.pack('!HH', 3, block_num) + chunk
                self.server_socket.sendto(packet, client_addr)
                try:
                    self.server_socket.settimeout(2.0)
                    ack, _ = self.server_socket.recvfrom(4)
                    ack_op, ack_block = struct.unpack('!HH', ack)
                    if ack_op != 4 or ack_block != block_num:
                        raise IOError("Bad ACK")
                except socket.timeout:
                    self.log.append("[ERROR] ACK timeout")
                    return
                except Exception:
                    return
                self.transfer_progress = int((block_num * block_size / total_size) * 100)
                block_num += 1
        self.log.append(f"[INFO] File sent ({total_size} bytes)")

    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.log.append("[INFO] Server stopped")

class NetworkManager:
    def __init__(self):
        self.original_settings = {}
        self.os_type = "auto"

    def detect_os(self):
        if self.os_type == "auto":
            return "windows" if sys.platform == "win32" else "linux"
        return self.os_type

    def set_os_mode(self, mode):
        self.os_type = mode

    def get_ethernet_interfaces(self):
        if self.detect_os() == "windows":
            return self._get_win_interfaces()
        return self._get_linux_interfaces()

    def _get_win_interfaces(self):
        interfaces = []
        try:
            output = subprocess.check_output('netsh interface show interface', shell=True,
                                           stderr=subprocess.DEVNULL).decode("cp866", errors="ignore")
            for line in output.splitlines():
                if "Connected" in line or "Подключено" in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        interfaces.append(parts[-1])
        except:
            pass
        if not interfaces:
            try:
                output = subprocess.check_output('wmic nic get NetConnectionID', shell=True,
                                               stderr=subprocess.DEVNULL).decode("cp866", errors="ignore")
                for line in output.splitlines():
                    line = line.strip()
                    if line and "NetConnectionID" not in line:
                        interfaces.append(line)
            except:
                pass
        return interfaces if interfaces else ["Ethernet"]

    def _get_linux_interfaces(self):
        interfaces = []
        for cmd in [["ip", "-o", "link", "show"], ["ls", "/sys/class/net"]]:
            try:
                output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode()
                if "/sys" in cmd[0]:
                    interfaces = [i.strip() for i in output.split() if i.strip() != "lo"]
                else:
                    for line in output.splitlines():
                        if ": " in line:
                            iface = line.split(": ")[1].split(":")[0].split("@")[0]
                            if iface != "lo":
                                interfaces.append(iface)
                if interfaces:
                    break
            except:
                continue
        return interfaces if interfaces else ["eth0"]

    def detect_active_ethernet(self):
        if self.detect_os() == "windows":
            try:
                output = subprocess.check_output('netsh interface show interface', shell=True,
                                               stderr=subprocess.DEVNULL).decode("cp866", errors="ignore")
                for line in output.splitlines():
                    if "Connected" in line or "Подключено" in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            return parts[-1]
            except:
                pass
        else:
            try:
                output = subprocess.check_output(["ip", "-o", "link", "show"], stderr=subprocess.DEVNULL).decode()
                for line in output.splitlines():
                    if "state UP" in line:
                        return line.split(": ")[1].split(":")[0].split("@")[0]
            except:
                pass
        return None

    def set_static_ip(self, interface, ip, netmask="255.255.255.0"):
        if self.detect_os() == "windows":
            return self._set_ip_windows(interface, ip, netmask)
        return self._set_ip_linux(interface, ip, netmask)

    def _set_ip_windows(self, interface, ip, netmask):
        try:
            output = subprocess.check_output(f'netsh interface ip show config name="{interface}"',
                                           shell=True, stderr=subprocess.DEVNULL).decode("cp866", errors="ignore")
            self.original_settings[interface] = output
            subprocess.check_call(f'netsh interface ip set address name="{interface}" static {ip} {netmask}',
                                shell=True, stderr=subprocess.DEVNULL)
            return True, f"IP {ip} set on {interface}"
        except subprocess.CalledProcessError as e:
            return False, str(e)

    def _set_ip_linux(self, interface, ip, netmask="255.255.255.0"):
        try:
            output = subprocess.check_output(["ip", "addr", "show", "dev", interface],
                                           stderr=subprocess.DEVNULL).decode()
            self.original_settings[interface] = output
            prefix = sum(bin(int(x)).count('1') for x in netmask.split('.'))
            subprocess.check_call(["ip", "addr", "add", f"{ip}/{prefix}", "dev", interface],
                                stderr=subprocess.DEVNULL)
            subprocess.check_call(["ip", "link", "set", "dev", interface, "up"], stderr=subprocess.DEVNULL)
            return True, f"IP {ip}/{prefix} set on {interface}"
        except subprocess.CalledProcessError as e:
            return False, str(e)

    def allow_port_69(self, port=69):
        if self.detect_os() == "windows":
            try:
                result = subprocess.run(f'netsh advfirewall firewall show rule name="TFTP Recovery Port {port}"',
                                      shell=True, capture_output=True, text=True)
                if "Нет правил" in result.stdout or "No rules" in result.stdout:
                    subprocess.check_call(f'netsh advfirewall firewall add rule name="TFTP Recovery Port {port}" '
                                        f'dir=in action=allow protocol=udp localport={port}', shell=True)
            except:
                pass
        else:
            try:
                subprocess.check_call(f"sudo iptables -A INPUT -p udp --dport {port} -j ACCEPT",
                                    shell=True, stderr=subprocess.DEVNULL)
            except:
                pass

    def restore_firewall(self, port=69):
        if self.detect_os() == "windows":
            try:
                subprocess.call(f'netsh advfirewall firewall delete rule name="TFTP Recovery Port {port}"',
                              shell=True, stderr=subprocess.DEVNULL)
            except:
                pass
        else:
            try:
                subprocess.call(f"sudo iptables -D INPUT -p udp --dport {port} -j ACCEPT",
                              shell=True, stderr=subprocess.DEVNULL)
            except:
                pass

    def restore_original_settings(self):
        if not self.original_settings:
            return
        if self.detect_os() == "windows":
            for iface in self.original_settings:
                try:
                    subprocess.call(f'netsh interface ip set address name="{iface}" dhcp',
                                  shell=True, stderr=subprocess.DEVNULL)
                except:
                    pass
        else:
            for iface in self.original_settings:
                try:
                    subprocess.call(["ip", "addr", "flush", "dev", iface], stderr=subprocess.DEVNULL)
                    subprocess.call(["ip", "link", "set", "dev", iface, "up"], stderr=subprocess.DEVNULL)
                except:
                    pass
        self.original_settings.clear()

def check_for_updates():
    try:
        req = Request("https://api.github.com/repos/yourname/tftp-recovery/releases/latest",
                     headers={"User-Agent": "TFTPRecovery"})
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return {"update_available": True, "version": data["tag_name"], "url": data["html_url"]}
    except:
        return {"update_available": False}

class ModernButton(tk.Canvas):
    def __init__(self, parent, text, icon="", command=None, width=160, height=40,
                 bg=ACCENT, hover_bg=ACCENT_HOVER, fg=TEXT_PRIMARY, font_size=11, radius=12):
        super().__init__(parent, width=width, height=height, bg=BG_COLOR, highlightthickness=0)
        self.command = command
        self.bg = bg
        self.hover_bg = hover_bg
        self.fg = fg
        self.radius = radius
        self.width = width
        self.height = height
        self.font = ("Segoe UI", font_size, "bold")
        self.display_text = f"{icon}{text}"
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.draw_button(self.bg)

    def draw_button(self, color):
        self.delete("all")
        self.create_rounded_rect(0, 0, self.width, self.height, self.radius, fill=color)
        self.create_text(self.width/2, self.height/2, text=self.display_text,
                        fill=self.fg, font=self.font)

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2, x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]
        return self.create_polygon(points, smooth=True, **kwargs)

    def on_enter(self, e):
        self.draw_button(self.hover_bg)

    def on_leave(self, e):
        self.draw_button(self.bg)

    def on_click(self, e):
        if self.command:
            self.command()

class App:
    def __init__(self):
        self.lang = "ru"
        self.tr = LANGUAGES[self.lang]
        self.server = None
        self.network = NetworkManager()
        self.folder_path = ""
        self.custom_ip = "192.168.1.88"
        self.custom_port = "69"
        self.custom_file = "recovery.bin"

        with open("models.json", "r", encoding="utf-8") as f:
            self.models = json.load(f)

        self.root = tk.Tk()
        self.root.title(self.tr["title"])
        self.root.geometry("950x780")
        self.root.minsize(900, 720)
        self.root.configure(bg=BG_COLOR)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.build_ui()
        self.root.after(100, self.update_log)
        self.root.after(200, self.update_progress)

    def build_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background=BG_COLOR, foreground=TEXT_PRIMARY, fieldbackground=INPUT_BG,
                       borderwidth=0, relief="flat")
        style.configure('TLabel', background=BG_COLOR, foreground=TEXT_PRIMARY)
        style.configure('TFrame', background=BG_COLOR)
        style.map('TCombobox', fieldbackground=[('readonly', INPUT_BG)], foreground=[('readonly', TEXT_PRIMARY)])
        style.configure('TEntry', fieldbackground=INPUT_BG, foreground=TEXT_PRIMARY, insertcolor=TEXT_PRIMARY)
        style.configure('TLabelframe', background=BG_COLOR, foreground=TEXT_PRIMARY, borderwidth=1, relief="solid")
        style.configure('TLabelframe.Label', background=BG_COLOR, foreground=TEXT_PRIMARY)
        style.configure('TProgressbar', background=ACCENT, troughcolor=INPUT_BG, borderwidth=0)

        main_frame = tk.Frame(self.root, bg=BG_COLOR, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        header_frame = tk.Frame(main_frame, bg=BG_COLOR)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(header_frame, text="📡 Router Recovery Tool", font=("Segoe UI", 20, "bold"),
                bg=BG_COLOR, fg=ACCENT_LIGHT).pack(side=tk.LEFT)
        self.lang_btn = ModernButton(header_frame, "", icon=ICONS["lang_en"],
                                     command=self.toggle_language, width=50, height=35,
                                     bg=CARD_BG, hover_bg=INPUT_BG, font_size=14)
        self.lang_btn.pack(side=tk.RIGHT, padx=5)

        top_card = tk.Frame(main_frame, bg=CARD_BG, padx=15, pady=15,
                           highlightbackground=BORDER, highlightthickness=1)
        top_card.pack(fill=tk.X, pady=(0, 10))
        tk.Label(top_card, text=self.tr["select_folder"], font=("Segoe UI", 11),
                bg=CARD_BG, fg=TEXT_SECONDARY).pack(anchor="w")
        folder_frame = tk.Frame(top_card, bg=CARD_BG)
        folder_frame.pack(fill=tk.X, pady=(8, 0))
        self.folder_var = tk.StringVar(value=self.folder_path)
        folder_entry = tk.Entry(folder_frame, textvariable=self.folder_var, state="readonly",
                               bg=INPUT_BG, fg=TEXT_PRIMARY, font=("Segoe UI", 10),
                               relief="flat", insertbackground=TEXT_PRIMARY)
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 8))
        ModernButton(folder_frame, ICONS["folder"], width=40, height=36, bg=ACCENT,
                    command=self.select_folder).pack(side=tk.LEFT, padx=3)
        ModernButton(folder_frame, self.tr["start"], width=165, height=36, bg=SUCCESS,
                    command=self.toggle_server).pack(side=tk.LEFT, padx=3)
        ModernButton(folder_frame, self.tr["wizard"], width=165, height=36, bg=ACCENT,
                    command=self.open_wizard).pack(side=tk.LEFT)

        settings_card = tk.Frame(main_frame, bg=CARD_BG, padx=15, pady=15,
                                highlightbackground=BORDER, highlightthickness=1)
        settings_card.pack(fill=tk.X, pady=(0, 10))
        tk.Label(settings_card, text=self.tr["settings"], font=("Segoe UI", 13, "bold"),
                bg=CARD_BG, fg=TEXT_PRIMARY).pack(anchor="w", pady=(0, 10))

        row1 = tk.Frame(settings_card, bg=CARD_BG)
        row1.pack(fill=tk.X, pady=3)
        tk.Label(row1, text=self.tr["network_interface"], font=("Segoe UI", 10),
                bg=CARD_BG, fg=TEXT_SECONDARY, width=18, anchor="w").pack(side=tk.LEFT)
        interfaces = self.network.get_ethernet_interfaces()
        self.iface_var = tk.StringVar(value=interfaces[0] if interfaces else "eth0")
        self.iface_combo = ttk.Combobox(row1, textvariable=self.iface_var, values=interfaces,
                                        state="readonly", width=25, font=("Segoe UI", 10))
        self.iface_combo.pack(side=tk.LEFT, padx=5)
        ModernButton(row1, self.tr["auto_detect"], width=60, height=30, bg=INPUT_BG,
                    hover_bg=BORDER, font_size=9, command=self.auto_detect_interface).pack(side=tk.LEFT, padx=5)

        row2 = tk.Frame(settings_card, bg=CARD_BG)
        row2.pack(fill=tk.X, pady=3)
        tk.Label(row2, text=self.tr["os_mode"], font=("Segoe UI", 10),
                bg=CARD_BG, fg=TEXT_SECONDARY, width=18, anchor="w").pack(side=tk.LEFT)
        self.os_var = tk.StringVar(value="auto")
        os_combo = ttk.Combobox(row2, textvariable=self.os_var,
                               values=["auto", "windows", "linux"], state="readonly", width=25,
                               font=("Segoe UI", 10))
        os_combo.pack(side=tk.LEFT, padx=5)
        os_combo.bind("<<ComboboxSelected>>", self.on_os_change)

        row3 = tk.Frame(settings_card, bg=CARD_BG)
        row3.pack(fill=tk.X, pady=3)
        tk.Label(row3, text=self.tr["model_select"], font=("Segoe UI", 10),
                bg=CARD_BG, fg=TEXT_SECONDARY, width=18, anchor="w").pack(side=tk.LEFT)
        model_names = [m["name"] for m in self.models]
        self.model_var = tk.StringVar(value=model_names[0] if model_names else "")
        self.model_combo = ttk.Combobox(row3, textvariable=self.model_var, values=model_names,
                                        state="readonly", width=25, font=("Segoe UI", 10))
        self.model_combo.pack(side=tk.LEFT, padx=5)
        self.model_combo.bind("<<ComboboxSelected>>", self.update_model_info)
        self.model_info = tk.Label(settings_card, text="", font=("Segoe UI", 9),
                                  bg=CARD_BG, fg=TEXT_SECONDARY)
        self.model_info.pack(anchor="w", pady=(5, 0))
        self.update_model_info(None)

        progress_frame = tk.Frame(settings_card, bg=CARD_BG)
        progress_frame.pack(fill=tk.X, pady=(8, 5))
        tk.Label(progress_frame, text=self.tr["progress"], font=("Segoe UI", 10),
                bg=CARD_BG, fg=TEXT_SECONDARY).pack(side=tk.LEFT)
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                           maximum=100, length=300)
        self.progress_bar.pack(side=tk.LEFT, padx=8)
        self.progress_label = tk.Label(progress_frame, text="0%", font=("Segoe UI", 10, "bold"),
                                      bg=CARD_BG, fg=SUCCESS)
        self.progress_label.pack(side=tk.LEFT)

        log_card = tk.Frame(main_frame, bg=CARD_BG, padx=15, pady=15,
                           highlightbackground=BORDER, highlightthickness=1)
        log_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        tk.Label(log_card, text=self.tr["log"], font=("Segoe UI", 13, "bold"),
                bg=CARD_BG, fg=TEXT_PRIMARY).pack(anchor="w", pady=(0, 8))
        self.log_text = scrolledtext.ScrolledText(log_card, height=10, state="disabled", wrap="word",
                                                  bg=INPUT_BG, fg=TEXT_PRIMARY, font=("Consolas", 9),
                                                  insertbackground=TEXT_PRIMARY, relief="flat",
                                                  borderwidth=0)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.error_var = tk.StringVar(value=f"{self.tr['error_line']}{self.tr['no_error']}")
        tk.Label(log_card, textvariable=self.error_var, font=("Segoe UI", 9),
                bg=CARD_BG, fg=ERROR, anchor="w").pack(fill=tk.X, pady=(8, 0))

        bottom_frame = tk.Frame(main_frame, bg=BG_COLOR)
        bottom_frame.pack(fill=tk.X)
        self.custom_btn = ModernButton(bottom_frame, self.tr["custom_settings"], width=140, height=34,
                                       bg=CARD_BG, hover_bg=INPUT_BG, font_size=10,
                                       command=self.open_custom_settings)
        self.custom_btn.pack(side=tk.LEFT, padx=3)
        ModernButton(bottom_frame, self.tr["update"], width=140, height=34,
                    bg=CARD_BG, hover_bg=INPUT_BG, font_size=10,
                    command=self.check_update).pack(side=tk.LEFT, padx=3)
        self.status_label = tk.Label(bottom_frame, text=self.tr["ready"], font=("Segoe UI", 9),
                                    bg=BG_COLOR, fg=SUCCESS)
        self.status_label.pack(side=tk.RIGHT, padx=10)

    def select_folder(self):
        folder = filedialog.askdirectory(title=self.tr["select_folder"])
        if folder:
            self.folder_path = folder
            self.folder_var.set(folder)

    def auto_detect_interface(self):
        iface = self.network.detect_active_ethernet()
        if iface:
            self.iface_var.set(iface)
            self.status_label.config(text=f"✅ {iface}")
        else:
            messagebox.showwarning(self.tr["warning"], "Не найден активный интерфейс")

    def on_os_change(self, event):
        mode = self.os_var.get()
        self.network.set_os_mode(mode)
        interfaces = self.network.get_ethernet_interfaces()
        self.iface_combo["values"] = interfaces
        if interfaces:
            self.iface_var.set(interfaces[0])
        self.build_ui()

    def update_model_info(self, event):
        name = self.model_var.get()
        for m in self.models:
            if m["name"] == name:
                self.model_info.config(text=f"IP: {m['ip']} | Порт: {m['port']} | Файл: {m['file']}\n{m.get('notes', '')}")
                self.custom_ip = m['ip']
                self.custom_port = str(m['port'])
                self.custom_file = m['file']
                return

    def toggle_server(self):
        if self.server and self.server.running:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        if not self.folder_path or not os.path.isdir(self.folder_path):
            messagebox.showerror(self.tr["error"], self.tr["select_folder_error"])
            return
        iface = self.iface_var.get()
        if not iface:
            messagebox.showerror(self.tr["error"], self.tr["no_interface"])
            return

        ip = self.custom_ip
        port = int(self.custom_port)
        success, msg = self.network.set_static_ip(iface, ip)
        if not success:
            messagebox.showerror(self.tr["error"], msg)
            return
        self.network.allow_port_69(port)
        self.server = PureTftpServer(self.folder_path, port)
        self.server.start()
        self.log(self.tr["server_started"].format(port=port), SUCCESS)
        self.error_var.set(f"{self.tr['error_line']}{self.tr['no_error']}")
        self.status_label.config(text=f"▶ Порт {port}")
        self.build_ui()

    def stop_server(self):
        if self.server:
            self.server.stop()
            self.server = None
        self.network.restore_original_settings()
        self.network.restore_firewall(int(self.custom_port))
        self.log(self.tr["server_stopped"], TEXT_SECONDARY)
        self.status_label.config(text=self.tr["ready"])
        self.build_ui()

    def log(self, text, color=TEXT_PRIMARY):
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def update_log(self):
        if self.server:
            for line in self.server.log[:]:
                self.server.log.remove(line)
                if "ERROR" in line:
                    self.error_var.set(f"{self.tr['error_line']}{line}")
                    self.log(line, ERROR)
                elif "WARN" in line:
                    self.log(line, WARNING)
                else:
                    self.log(line, TEXT_SECONDARY)
        self.root.after(100, self.update_log)

    def update_progress(self):
        if self.server and self.server.running:
            p = self.server.transfer_progress
            self.progress_var.set(p)
            self.progress_label.config(text=f"{p}%")
        self.root.after(200, self.update_progress)

    def open_wizard(self):
        steps = WIZARD_STEPS[self.lang]
        cur = [0]
        win = tk.Toplevel(self.root, bg=BG_COLOR)
        win.title(self.tr["wizard"])
        win.geometry("550x350")
        win.resizable(False, False)
        title_lbl = tk.Label(win, text="", font=("Segoe UI", 14, "bold"), bg=BG_COLOR, fg=TEXT_PRIMARY)
        title_lbl.pack(pady=(25, 10))
        desc_lbl = tk.Label(win, text="", wraplength=450, font=("Segoe UI", 11), bg=BG_COLOR, fg=TEXT_SECONDARY)
        desc_lbl.pack(pady=10)
        indicator_lbl = tk.Label(win, text="", font=("Segoe UI", 9), bg=BG_COLOR, fg=TEXT_SECONDARY)
        indicator_lbl.pack(pady=10)
        btn_frame = tk.Frame(win, bg=BG_COLOR)
        btn_frame.pack(pady=20)

        def update():
            i = cur[0]
            title_lbl.config(text=steps[i][0])
            desc_lbl.config(text=steps[i][1])
            indicator_lbl.config(text=f"{i+1}/{len(steps)}")
            btn_prev["state"] = "normal" if i > 0 else "disabled"
            btn_next.config(text="✅ Готово" if i == len(steps)-1 else "Далее →")

        def next_step():
            if cur[0] < len(steps)-1:
                cur[0] += 1
                update()
            else:
                win.destroy()

        def prev_step():
            if cur[0] > 0:
                cur[0] -= 1
                update()

        btn_prev = tk.Button(btn_frame, text="← Назад", command=prev_step, state="disabled",
                            bg=INPUT_BG, fg=TEXT_PRIMARY, font=("Segoe UI", 10),
                            relief="flat", padx=15, pady=5, cursor="hand2")
        btn_prev.pack(side=tk.LEFT, padx=5)
        btn_next = tk.Button(btn_frame, text="Далее →", command=next_step,
                            bg=ACCENT, fg=TEXT_PRIMARY, font=("Segoe UI", 10),
                            relief="flat", padx=15, pady=5, cursor="hand2")
        btn_next.pack(side=tk.LEFT, padx=5)
        update()

    def open_custom_settings(self):
        win = tk.Toplevel(self.root, bg=BG_COLOR)
        win.title(self.tr["custom_settings"])
        win.geometry("400x280")
        win.resizable(False, False)
        tk.Label(win, text=self.tr["custom_settings"], font=("Segoe UI", 14, "bold"),
                bg=BG_COLOR, fg=TEXT_PRIMARY).pack(pady=(20, 15))
        fields = [
            (self.tr["custom_ip"], "custom_ip"),
            (self.tr["custom_port"], "custom_port"),
            (self.tr["custom_file"], "custom_file"),
        ]
        entries = {}
        for label, key in fields:
            frame = tk.Frame(win, bg=BG_COLOR)
            frame.pack(fill=tk.X, padx=30, pady=5)
            tk.Label(frame, text=label, font=("Segoe UI", 10), bg=BG_COLOR, fg=TEXT_SECONDARY,
                    width=12, anchor="w").pack(side=tk.LEFT)
            var = tk.StringVar(value=getattr(self, key))
            entry = tk.Entry(frame, textvariable=var, bg=INPUT_BG, fg=TEXT_PRIMARY,
                           font=("Segoe UI", 10), relief="flat", insertbackground=TEXT_PRIMARY)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
            entries[key] = var
        btn_frame = tk.Frame(win, bg=BG_COLOR)
        btn_frame.pack(pady=20)

        def save():
            self.custom_ip = entries["custom_ip"].get()
            self.custom_port = entries["custom_port"].get()
            self.custom_file = entries["custom_file"].get()
            self.status_label.config(text=self.tr["custom_saved"])
            win.destroy()

        tk.Button(btn_frame, text=self.tr["save_custom"], command=save,
                 bg=SUCCESS, fg=TEXT_PRIMARY, font=("Segoe UI", 10, "bold"),
                 relief="flat", padx=20, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text=self.tr["cancel"], command=win.destroy,
                 bg=INPUT_BG, fg=TEXT_PRIMARY, font=("Segoe UI", 10),
                 relief="flat", padx=20, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=5)

    def toggle_language(self):
        self.lang = "en" if self.lang == "ru" else "ru"
        self.tr = LANGUAGES[self.lang]
        self.root.title(self.tr["title"])
        self.build_ui()

    def check_update(self):
        result = check_for_updates()
        if result["update_available"]:
            messagebox.showinfo(self.tr["update"],
                              f"Доступна версия {result['version']}\n{result['url']}")
        else:
            messagebox.showinfo(self.tr["update"], "У вас последняя версия")

    def on_closing(self):
        if self.server:
            self.server.stop()
            self.network.restore_original_settings()
            self.network.restore_firewall(int(self.custom_port))
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    App().run()