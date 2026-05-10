import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import json
import threading
import socket
import subprocess
import sys
import time
import struct
from urllib.request import urlopen, Request

import base64, tempfile, os

ICON_BASE64 = """
AAABAAEAEBAAAAAAIABoBAAAFgAAACgAAAAQAAAAIAAAAAEAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD///8A////AP///wD///8A////AP///wD///8A
////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////
AP///wD///8A////AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
"""

def set_app_icon(root):
   
    tmp = tempfile.NamedTemporaryFile(suffix='.ico', delete=False)
    tmp.write(base64.b64decode(ICON_BASE64))
    tmp.close()
    root.iconbitmap(tmp.name)
    os.unlink(tmp.name)   # сразу можно удалить, иконка уже загружена в окно

LANGUAGES = {
    "ru": {
        "title": "Восстановление роутера",
        "select_folder": "Выбрать папку с recovery.bin",
        "start": "Запустить сервер",
        "stop": "Остановить сервер",
        "settings": "Настройки",
        "network_interface": "Сетевой интерфейс",
        "static_ip": "Статический IP (192.168.1.88)",
        "model_select": "Модель роутера",
        "log": "Лог",
        "error_line": "Последняя ошибка: ",
        "no_error": "Нет ошибок",
        "update": "Проверить обновления",
        "lang_toggle": "English",
        "auto_detect": "Авто",
        "wizard": "Мастер восстановления",
        "progress": "Прогресс передачи",
        "warning": "Предупреждение",
        "error": "Ошибка",
        "info": "Информация",
        "select_folder_error": "Выберите папку с прошивкой",
        "recovery_not_found": "Файл recovery.bin не найден",
        "no_interface": "Не выбран сетевой интерфейс",
        "server_started": "Сервер запущен, ожидание запросов...",
        "server_stopped": "Сервер остановлен, сеть восстановлена.",
    },
    "en": {
        "title": "Router Recovery",
        "select_folder": "Select folder with recovery.bin",
        "start": "Start Server",
        "stop": "Stop Server",
        "settings": "Settings",
        "network_interface": "Network Interface",
        "static_ip": "Static IP (192.168.1.88)",
        "model_select": "Router Model",
        "log": "Log",
        "error_line": "Last error: ",
        "no_error": "No errors",
        "update": "Check for updates",
        "lang_toggle": "Русский",
        "auto_detect": "Auto",
        "wizard": "Recovery Wizard",
        "progress": "Transfer Progress",
        "warning": "Warning",
        "error": "Error",
        "info": "Information",
        "select_folder_error": "Please select firmware folder",
        "recovery_not_found": "recovery.bin not found",
        "no_interface": "No network interface selected",
        "server_started": "Server started, waiting for requests...",
        "server_stopped": "Server stopped, network restored.",
    }
}

WIZARD_STEPS = {
    "ru": [
        ("Шаг 1: Подключение кабеля", "Подключите Ethernet-кабель к LAN-порту роутера."),
        ("Шаг 2: Настройка питания", "Отключите питание роутера. Нажмите и удерживайте кнопку Reset."),
        ("Шаг 3: Подача питания", "Включите питание роутера, продолжая удерживать Reset 10 секунд."),
        ("Шаг 4: Ожидание запроса", "Сервер ожидает запрос от роутера. LAN-индикатор должен мигать."),
        ("Шаг 5: Завершение", "После загрузки прошивки роутер перезагрузится. Можно отключить кабель."),
    ],
    "en": [
        ("Step 1: Connect cable", "Connect Ethernet cable to the LAN port of the router."),
        ("Step 2: Power off", "Power off the router. Press and hold the Reset button."),
        ("Step 3: Power on", "Power on the router while still holding Reset for 10 seconds."),
        ("Step 4: Wait for request", "Server is waiting for router request. LAN LED should blink."),
        ("Step 5: Completion", "After firmware upload, the router will reboot. You may disconnect."),
    ]
}

class PureTftpServer:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.server_socket = None
        self.running = False
        self.log = []
        self.transfer_progress = 0

    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server_socket.bind(('0.0.0.0', 69))
        except Exception as e:
            self.log.append(f"[ERROR] Не удалось занять порт 69: {e}")
            self.running = False
            return
        self.log.append("[INFO] TFTP сервер запущен на порту 69")
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
                self.log.append(f"[ERROR] {e}")

    def _handle_request(self, data, client_addr):
        try:
            opcode = struct.unpack('!H', data[:2])[0]
            if opcode == 1:  # RRQ
                filename, mode = self._parse_rrq(data)
                if mode not in (b'octet', b'netascii'):
                    self._send_error(client_addr, 0, "Unsupported mode")
                    return
                filepath = os.path.join(self.root_dir, filename.decode())
                if not os.path.isfile(filepath):
                    self._send_error(client_addr, 1, "File not found")
                    return
                self.log.append(f"[INFO] Запрос файла {filename.decode()} от {client_addr}")
                self._send_file(client_addr, filepath)
            else:
                self._send_error(client_addr, 4, "Operation not supported")
        except Exception as e:
            self.log.append(f"[ERROR] Обработка запроса: {e}")

    def _parse_rrq(self, data):
        parts = data[2:].split(b'\x00')
        if len(parts) < 2:
            raise ValueError("Invalid RRQ")
        return parts[0], parts[1].lower()

    def _send_error(self, client_addr, code, msg):
        packet = struct.pack('!HH', 5, code) + msg.encode() + b'\x00'
        self.server_socket.sendto(packet, client_addr)

    def _send_file(self, client_addr, filepath):
        total_size = os.path.getsize(filepath)
        block_size = 512
        self.transfer_progress = 0
        with open(filepath, 'rb') as f:
            block_num = 1
            while True:
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
                    self.log.append("[ERROR] Timeout ожидания ACK")
                    return
                self.transfer_progress = int((block_num * block_size / total_size) * 100)
                block_num += 1
        self.log.append(f"[INFO] Файл передан ({total_size} байт)")

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
            self.log.append("[INFO] Сервер остановлен")

class NetworkManager:
    def __init__(self):
        self.original_settings = {}

    def get_ethernet_interfaces(self):
        if sys.platform == "win32":
            try:
                output = subprocess.check_output(
                    'wmic nic where "AdapterTypeId=0 AND NetEnabled=True" get NetConnectionID /value',
                    shell=True
                ).decode("cp866", errors="ignore")
                return [line.split("=",1)[1].strip() for line in output.splitlines() if "=" in line and line.split("=",1)[1].strip()] or ["Ethernet"]
            except:
                return ["Ethernet"]
        else:
            try:
                output = subprocess.check_output(["ip", "-o", "link", "show"]).decode()
                return [line.split(":")[1].strip() for line in output.splitlines() if "ether" in line]
            except:
                return []

    def detect_active_ethernet(self):
        if sys.platform == "win32":
            try:
                output = subprocess.check_output(
                    'wmic nic where "AdapterTypeId=0 AND NetEnabled=True" get NetConnectionID /value',
                    shell=True
                ).decode("cp866", errors="ignore")
                for line in output.splitlines():
                    if "=" in line:
                        name = line.split("=",1)[1].strip()
                        if name:
                            return name
            except:
                pass
        else:
            try:
                output = subprocess.check_output(["ip", "-o", "link", "show"]).decode()
                for line in output.splitlines():
                    if "ether" in line and "UP" in line:
                        return line.split(":")[1].strip()
            except:
                pass
        return None

    def set_static_ip(self, interface, ip, netmask="255.255.255.0"):
        if sys.platform == "win32":
            try:
                output = subprocess.check_output(f'netsh interface ip show config name="{interface}"', shell=True).decode("cp866")
                self.original_settings[interface] = output
                subprocess.check_call(f'netsh interface ip set address name="{interface}" static {ip} {netmask}', shell=True)
                return True, f"Установлен IP {ip} на {interface}"
            except subprocess.CalledProcessError as e:
                return False, f"Ошибка netsh: {e}"
        else:
            try:
                output = subprocess.check_output(["ip", "addr", "show", "dev", interface]).decode()
                self.original_settings[interface] = output
                prefix = sum(bin(int(x)).count('1') for x in netmask.split('.'))
                subprocess.check_call(["ip", "addr", "add", f"{ip}/{prefix}", "dev", interface])
                subprocess.check_call(["ip", "link", "set", "dev", interface, "up"])
                return True, f"Установлен IP {ip}/{prefix} на {interface}"
            except subprocess.CalledProcessError as e:
                return False, f"Ошибка ip: {e}"

    def allow_port_69(self):
        if sys.platform == "win32":
            try:
                result = subprocess.run('netsh advfirewall firewall show rule name="TFTP Recovery Port 69"', shell=True, capture_output=True, text=True)
                if "Нет правил" in result.stdout or "No rules" in result.stdout:
                    subprocess.check_call('netsh advfirewall firewall add rule name="TFTP Recovery Port 69" dir=in action=allow protocol=udp localport=69', shell=True)
                return True, "Правило брандмауэра добавлено"
            except:
                return False, "Ошибка настройки брандмауэра"
        else:
            try:
                subprocess.check_call("sudo iptables -A INPUT -p udp --dport 69 -j ACCEPT", shell=True)
                return True, "Правило iptables добавлено"
            except:
                return False, "Ошибка iptables"

    def restore_firewall(self):
        if sys.platform == "win32":
            try:
                subprocess.call('netsh advfirewall firewall delete rule name="TFTP Recovery Port 69"', shell=True)
            except:
                pass
        else:
            try:
                subprocess.call("sudo iptables -D INPUT -p udp --dport 69 -j ACCEPT", shell=True)
            except:
                pass

    def restore_original_settings(self):
        if sys.platform == "win32":
            for iface in self.original_settings:
                try:
                    subprocess.call(f'netsh interface ip set address name="{iface}" dhcp', shell=True)
                except:
                    pass
        else:
            for iface in self.original_settings:
                try:
                    subprocess.call(["ip", "addr", "flush", "dev", iface])
                    subprocess.call(["ip", "link", "set", "dev", iface, "up"])
                except:
                    pass

def check_for_updates():
    CURRENT_VERSION = "1.0.0"
    REPO_API_URL = "https://api.github.com/repos/dev-sakura-dev/tftp-recovery/releases/latest"
    try:
        req = Request(REPO_API_URL, headers={"User-Agent": "TFTPRecovery"})
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            latest = data["tag_name"].lstrip("v")
            if latest > CURRENT_VERSION:
                return {"update_available": True, "version": latest, "url": data["html_url"]}
    except:
        pass
    return {"update_available": False}

class App:
    def __init__(self):
        self.lang = "ru"
        self.tr = LANGUAGES[self.lang]
        self.server = None
        self.network = NetworkManager()
        self.folder_path = ""

        with open("models.json", "r", encoding="utf-8") as f:
            self.models = json.load(f)

        self.root = tk.Tk()
        self.root.title(self.tr["title"])
        self.root.geometry("900x720")
        self.root.minsize(900, 700)
        self.root.configure(bg='#1e1e1e')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.build_ui()
        self.root.after(100, self.update_log)
        self.root.after(200, self.update_progress)

    def build_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background='#1e1e1e', foreground='white', fieldbackground='#2d2d2d')
        style.configure('TLabel', background='#1e1e1e', foreground='white')
        style.configure('TFrame', background='#1e1e1e')
        style.configure('TButton', background='#3a3a3a', foreground='white', borderwidth=0, focuscolor='none')
        style.map('TButton', background=[('active', '#6200ee')])
        style.configure('Primary.TButton', background='#6200ee', foreground='white')
        style.configure('Danger.TButton', background='#b00020', foreground='white')
        style.configure('TLabelframe', background='#1e1e1e', foreground='white')
        style.configure('TLabelframe.Label', background='#1e1e1e', foreground='white')
        style.configure('TEntry', fieldbackground='#2d2d2d', foreground='white')
        style.configure('TCombobox', fieldbackground='#2d2d2d', foreground='white', arrowcolor='white')
        style.map('TCombobox', fieldbackground=[('readonly', '#2d2d2d')], foreground=[('readonly', 'white')])
        style.configure('TProgressbar', background='#6200ee', troughcolor='#2d2d2d')

        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0,10))

        self.folder_var = tk.StringVar(value=self.folder_path)
        folder_entry = ttk.Entry(top_frame, textvariable=self.folder_var, state="readonly", width=50)
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))

        ttk.Button(top_frame, text="...", width=3, command=self.select_folder).pack(side=tk.LEFT, padx=5)
        self.start_btn = ttk.Button(top_frame, text=self.tr["start"], command=self.toggle_server, style='Primary.TButton')
        self.start_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text=self.tr["wizard"], command=self.open_wizard).pack(side=tk.LEFT, padx=5)

        settings_frame = ttk.LabelFrame(main_frame, text=self.tr["settings"], padding=10)
        settings_frame.pack(fill=tk.X, pady=(0,10))

        iface_frame = ttk.Frame(settings_frame)
        iface_frame.pack(fill=tk.X, pady=5)
        ttk.Label(iface_frame, text=self.tr["network_interface"]).pack(side=tk.LEFT)
        interfaces = self.network.get_ethernet_interfaces()
        self.iface_var = tk.StringVar(value=interfaces[0] if interfaces else "Ethernet")
        ttk.Combobox(iface_frame, textvariable=self.iface_var, values=interfaces, state="readonly", width=25).pack(side=tk.LEFT, padx=5)
        ttk.Button(iface_frame, text=self.tr["auto_detect"], command=self.auto_detect_interface).pack(side=tk.LEFT, padx=5)

        ip_frame = ttk.Frame(settings_frame)
        ip_frame.pack(fill=tk.X, pady=5)
        ttk.Label(ip_frame, text=self.tr["static_ip"]).pack(side=tk.LEFT)
        ttk.Label(ip_frame, text="192.168.1.88", foreground="#81c784", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=5)

        model_frame = ttk.Frame(settings_frame)
        model_frame.pack(fill=tk.X, pady=5)
        ttk.Label(model_frame, text=self.tr["model_select"]).pack(side=tk.LEFT)
        model_names = [m["name"] for m in self.models]
        self.model_var = tk.StringVar(value=model_names[0] if model_names else "")
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, values=model_names, state="readonly", width=25)
        self.model_combo.pack(side=tk.LEFT, padx=5)
        self.model_combo.bind("<<ComboboxSelected>>", self.update_model_info)
        self.model_info = ttk.Label(settings_frame, text="", foreground="#bdbdbd")
        self.model_info.pack(fill=tk.X, pady=(5,0))
        self.update_model_info(None)

        progress_frame = ttk.Frame(settings_frame)
        progress_frame.pack(fill=tk.X, pady=(5,0))
        ttk.Label(progress_frame, text=self.tr["progress"]).pack(side=tk.LEFT)
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, length=200)
        self.progress_bar.pack(side=tk.LEFT, padx=5)
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.pack(side=tk.LEFT)

        log_frame = ttk.LabelFrame(main_frame, text=self.tr["log"], padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0,10))
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, state="disabled", wrap="word", bg='#121212', fg='white', insertbackground='white')
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.error_var = tk.StringVar(value=f"{self.tr['error_line']}{self.tr['no_error']}")
        ttk.Label(log_frame, textvariable=self.error_var, foreground="#ff5252").pack(anchor="w", pady=(5,0))

        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X)
        ttk.Button(bottom_frame, text=self.tr["update"], command=self.check_update).pack(side=tk.LEFT)
        ttk.Button(bottom_frame, text=self.tr["lang_toggle"], command=self.toggle_language).pack(side=tk.RIGHT)

    def select_folder(self):
        folder = filedialog.askdirectory(title=self.tr["select_folder"])
        if folder:
            self.folder_path = folder
            self.folder_var.set(folder)

    def auto_detect_interface(self):
        iface = self.network.detect_active_ethernet()
        if iface:
            self.iface_var.set(iface)
            messagebox.showinfo(self.tr["info"], f"Выбран интерфейс: {iface}")
        else:
            messagebox.showwarning(self.tr["warning"], "Не найден активный Ethernet-интерфейс")

    def update_model_info(self, event):
        name = self.model_var.get()
        for m in self.models:
            if m["name"] == name:
                self.model_info.config(text=f"IP: {m['ip']} | Порт: {m['port']} | Файл: {m['file']}\n{m.get('notes', '')}")
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
        recovery_file = os.path.join(self.folder_path, "recovery.bin")
        if not os.path.isfile(recovery_file):
            messagebox.showwarning(self.tr["warning"], self.tr["recovery_not_found"])
        iface = self.iface_var.get()
        if not iface:
            messagebox.showerror(self.tr["error"], self.tr["no_interface"])
            return
        success, msg = self.network.set_static_ip(iface, "192.168.1.88", "255.255.255.0")
        if not success:
            messagebox.showerror(self.tr["error"], msg)
            return
        self.network.allow_port_69()
        self.server = PureTftpServer(self.folder_path)
        self.server.start()
        self.log(self.tr["server_started"], "green")
        self.error_var.set(f"{self.tr['error_line']}{self.tr['no_error']}")
        self.start_btn.config(text=self.tr["stop"], style='Danger.TButton')

    def stop_server(self):
        if self.server:
            self.server.stop()
            self.server = None
        self.network.restore_original_settings()
        self.network.restore_firewall()
        self.log(self.tr["server_stopped"], "green")
        self.start_btn.config(text=self.tr["start"], style='Primary.TButton')

    def log(self, text, color="white"):
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
                    self.log(line, "red")
                elif "WARN" in line:
                    self.log(line, "orange")
                else:
                    self.log(line, "white")
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
        win = tk.Toplevel(self.root, bg='#1e1e1e')
        win.title(self.tr["wizard"])
        win.geometry("500x300")
        win.resizable(False, False)

        title_lbl = tk.Label(win, text="", font=("Helvetica", 12, "bold"), bg='#1e1e1e', fg='white')
        title_lbl.pack(pady=10)
        desc_lbl = tk.Label(win, text="", wraplength=400, bg='#1e1e1e', fg='white')
        desc_lbl.pack(pady=10)
        indicator_lbl = tk.Label(win, text="", fg='grey', bg='#1e1e1e')
        indicator_lbl.pack(pady=5)

        btn_frame = tk.Frame(win, bg='#1e1e1e')
        btn_frame.pack(pady=10)

        def update():
            i = cur[0]
            title_lbl.config(text=steps[i][0])
            desc_lbl.config(text=steps[i][1])
            indicator_lbl.config(text=f"Шаг {i+1}/{len(steps)}" if self.lang == "ru" else f"Step {i+1}/{len(steps)}")
            prev_btn.config(state="normal" if i > 0 else "disabled")
            next_btn.config(text="Готово" if i == len(steps)-1 else ("Далее →" if self.lang == "ru" else "Next →"))

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

        prev_btn = tk.Button(btn_frame, text="← Назад" if self.lang == "ru" else "← Back", command=prev_step, state="disabled", bg='#3a3a3a', fg='white')
        prev_btn.pack(side=tk.LEFT, padx=5)
        next_btn = tk.Button(btn_frame, text="Далее →" if self.lang == "ru" else "Next →", command=next_step, bg='#6200ee', fg='white')
        next_btn.pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Закрыть" if self.lang == "ru" else "Close", command=win.destroy, bg='#3a3a3a', fg='white').pack(side=tk.LEFT, padx=5)
        update()

    def toggle_language(self):
        self.lang = "en" if self.lang == "ru" else "ru"
        self.tr = LANGUAGES[self.lang]
        self.root.title(self.tr["title"])
        self.build_ui()

    def check_update(self):
        result = check_for_updates()
        if result["update_available"]:
            messagebox.showinfo(self.tr["update"], f"Доступна версия {result['version']}\n{result['url']}")
        else:
            messagebox.showinfo(self.tr["update"], "У вас последняя версия" if self.lang == "ru" else "You have the latest version")

    def on_closing(self):
        if self.server:
            self.server.stop()
            self.network.restore_original_settings()
            self.network.restore_firewall()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    App().run()
