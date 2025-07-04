﻿import telebot
import subprocess
import pyautogui
import os
import pyperclip
import datetime
import threading
import time
import socket
import sounddevice as sd
import speech_recognition as sr
from pystray import Icon, MenuItem as item, Menu
from PIL import Image, ImageDraw

# -- CONFIG
CHAT_ID = os.getenv("CHAT_ID")
TOKEN = os.environ.get("BOT_TOKEN")
PIN_CODE = "360"
BASE_PATH = os.getcwd()
UPLOAD_FOLDER = os.path.join(BASE_PATH, "uploads")
LOG_FOLDER = os.path.join(BASE_PATH, "logs")
CHECK_INTERVAL = 3600
INACTIVITY_HOURS = 24

# -- INIT
bot = telebot.TeleBot(TOKEN)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)

last_command_time = time.time()
icon_instance = None
previous_ip = None

# == FUNCTIONS ==

def log_action(text):
    global last_command_time
    last_command_time = time.time()
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    filename = datetime.datetime.now().strftime('commands_%Y-%m-%d.log')
    with open(os.path.join(LOG_FOLDER, filename), 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {text}\n")

def format_size(size):
    return f"{size / (1024*1024):.1f} MB" if size > 1024*1024 else f"{size / 1024:.1f} KB"

def format_date(ts):
    return datetime.datetime.fromtimestamp(ts).strftime('%d/%m/%Y %H:%M')

def scan_folder(path):
    if not os.path.exists(path):
        return "Ã¢ÂÅ’ ÃŽÅ¸ Ãâ€ ÃŽÂ¬ÃŽÂºÃŽÂµÃŽÂ»ÃŽÂ¿Ãâ€š ÃŽÂ´ÃŽÂµÃŽÂ½ Ãâ€¦Ãâ‚¬ÃŽÂ¬ÃÂÃâ€¡ÃŽÂµÃŽÂ¹."
    try:
        entries = os.listdir(path)
        if not entries:
            return "Ã°Å¸â€œâ€š ÃŽÅ¸ Ãâ€ ÃŽÂ¬ÃŽÂºÃŽÂµÃŽÂ»ÃŽÂ¿Ãâ€š ÃŽÂµÃŽÂ¯ÃŽÂ½ÃŽÂ±ÃŽÂ¹ ÃŽÂ¬ÃŽÂ´ÃŽÂµÃŽÂ¹ÃŽÂ¿Ãâ€š."
        lines = [f"Ã°Å¸â€œÂ {path}"]
        for entry in entries:
            full = os.path.join(path, entry)
            if os.path.isfile(full):
                size = os.path.getsize(full)
                date = os.path.getmtime(full)
                lines.append(f"- {entry} | {format_size(size)} | {format_date(date)}")
        return "\n".join(lines)
    except Exception as e:
        return f"Ã¢Å¡Â Ã¯Â¸Â ÃŽÂ£Ãâ€ ÃŽÂ¬ÃŽÂ»ÃŽÂ¼ÃŽÂ± ÃŽÂºÃŽÂ±Ãâ€žÃŽÂ¬ Ãâ€žÃŽÂ¿ scan: {str(e)}"

def execute_command(command):
    try:
        result = subprocess.check_output(command, shell=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        return f"Ã¢ÂÅ’ ÃŽÂ£Ãâ€ ÃŽÂ¬ÃŽÂ»ÃŽÂ¼ÃŽÂ±:\n{e.output}"
    except Exception as e:
        return f"Ã¢Å¡Â Ã¯Â¸Â ÃŽâ€¢ÃŽÂ¾ÃŽÂ±ÃŽÂ¯ÃÂÃŽÂµÃÆ’ÃŽÂ·:\n{str(e)}"
def take_screenshot():
    try:
        path = os.path.join(BASE_PATH, "screen.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(path)
        return path
    except Exception:
        return None

def send_file(path, chat_id):
    try:
        if not os.path.exists(path):
            return False
        with open(path, 'rb') as f:
            bot.send_document(chat_id, f)
        return True
    except Exception:
        return False

def check_inactivity():
    while True:
        time.sleep(CHECK_INTERVAL)
        delta_hours = (time.time() - last_command_time) / 3600
        if delta_hours >= INACTIVITY_HOURS:
            today = datetime.datetime.now().strftime('commands_%Y-%m-%d.log')
            log_path = os.path.join(LOG_FOLDER, today)
            sent_flag = log_path + ".sent"
            if os.path.exists(log_path) and not os.path.exists(sent_flag):
                try:
                    with open(log_path, 'rb') as f:
                        bot.send_document(CHAT_ID, f, caption="Ã°Å¸â€¢â€œ 24h inactivity Ã¢â‚¬â€œ ÃŽÂ±Ãâ€¦Ãâ€žÃÅ’ÃŽÂ¼ÃŽÂ±Ãâ€žÃŽÂ¿ log")
                    open(sent_flag, 'w').close()
                except:
                    pass

def watch_network():
    global previous_ip
    while True:
        try:
            ip = socket.gethostbyname(socket.gethostname())
            if previous_ip and ip != previous_ip:
                bot.send_message(CHAT_ID, f"Ã°Å¸Å’Â ÃŽÂÃŽÂ­ÃŽÂ± IP ÃŽÂ±ÃŽÂ½ÃŽÂ¹Ãâ€¡ÃŽÂ½ÃŽÂµÃÂÃŽÂ¸ÃŽÂ·ÃŽÂºÃŽÂµ: {ip}")
                log_action(f"IP ÃŽÂ¬ÃŽÂ»ÃŽÂ»ÃŽÂ±ÃŽÂ¾ÃŽÂµ: {previous_ip} Ã¢â€ â€™ {ip}")
            previous_ip = ip
        except:
            pass
        time.sleep(180)
def recognize_speech():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    while True:
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio, language='el-GR')
            if command:
                log_action(f"Ã°Å¸Å½â„¢Ã¯Â¸Â ÃŽÂ¦Ãâ€°ÃŽÂ½ÃŽÂ®: {command}")
                output = execute_command(command)
                if output:
                    bot.send_message(CHAT_ID, f"Ã°Å¸â€”Â£Ã¯Â¸Â {command}\nÃ°Å¸â€œÂ¤ {output[:4000]}")
        except sr.UnknownValueError:
            continue
        except:
            time.sleep(5)

def create_icon():
    image = Image.new('RGB', (64, 64), (255, 0, 0))
    d = ImageDraw.Draw(image)
    d.rectangle((8, 8, 56, 56), fill=(0, 0, 0))
    return image

def show_status(icon, item):
    log_action("Tray: Show status clicked.")
    os.startfile(LOG_FOLDER)

def send_log_now(icon, item):
    try:
        today = datetime.datetime.now().strftime('commands_%Y-%m-%d.log')
        log_path = os.path.join(LOG_FOLDER, today)
        if os.path.exists(log_path):
            with open(log_path, 'rb') as f:
                bot.send_document(CHAT_ID, f, caption="Ã°Å¸â€œÂ ÃŽÂ§ÃŽÂµÃŽÂ¹ÃÂÃŽÂ¿ÃŽÂºÃŽÂ¯ÃŽÂ½ÃŽÂ·Ãâ€žÃŽÂ· ÃŽÂ±Ãâ‚¬ÃŽÂ¿ÃÆ’Ãâ€žÃŽÂ¿ÃŽÂ»ÃŽÂ® log")
    except:
        pass

def tray():
    global icon_instance
    icon_instance = Icon("Lucien", create_icon(), "Lucien", menu=Menu(
        item('Ã°Å¸â€œÂ¤ Send Log Now', send_log_now),
        item('Ã°Å¸â€œÂ Show Status', show_status),
        item('Ã°Å¸â€â€™ Exit (PIN ÃŽÂ¼ÃÅ’ÃŽÂ½ÃŽÂ¿)', lambda icon, item: None)
    ))
    icon_instance.run()
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global icon_instance
    if message.chat.id != CHAT_ID:
        return

    command = message.text.strip()
    log_action(f"Command received: {command}")

    if command.startswith("/pin "):
        entered_pin = command[5:].strip()
        if entered_pin == PIN_CODE:
            bot.send_message(message.chat.id, "Ã°Å¸â€Â PIN OK. ÃŽÂ¤ÃŽÂµÃÂÃŽÂ¼ÃŽÂ±Ãâ€žÃŽÂ¹ÃÆ’ÃŽÂ¼ÃÅ’Ãâ€š Lucien...")
            log_action("Lucien exited via PIN.")
            if icon_instance:
                icon_instance.stop()
            os._exit(0)
        else:
            bot.send_message(message.chat.id, "Ã¢ÂÅ’ ÃŽâ€ºÃŽÂ¬ÃŽÂ¸ÃŽÂ¿Ãâ€š PIN.")
        return

    if command == "/screenshot":
        path = take_screenshot()
        if path:
            with open(path, 'rb') as photo:
                bot.send_photo(message.chat.id, photo)
            os.remove(path)
            log_action("Screenshot sent.")
        return

    if command.startswith("/get "):
        filename = command[5:].strip()
        if send_file(filename, message.chat.id):
            bot.send_message(message.chat.id, f"Ã°Å¸â€œÅ½ ÃŽâ€˜Ãâ‚¬ÃŽÂµÃÆ’Ãâ€žÃŽÂ¬ÃŽÂ»ÃŽÂ·: {filename}")
            log_action(f"File sent: {filename}")
        else:
            bot.send_message(message.chat.id, f"Ã¢ÂÅ’ ÃŽâ€ÃŽÂµÃŽÂ½ ÃŽÂ²ÃÂÃŽÂ­ÃŽÂ¸ÃŽÂ·ÃŽÂºÃŽÂµ: {filename}")
        return

    if command.startswith("/scan "):
        folder = command[6:].strip()
        result = scan_folder(folder)
        bot.send_message(message.chat.id, result)
        return

    if command == "/clip":
        try:
            clip = pyperclip.paste()
            bot.send_message(message.chat.id, f"Ã°Å¸â€œâ€¹ Clipboard:\n{clip}")
            log_action("Clipboard sent.")
        except Exception as e:
            bot.send_message(message.chat.id, f"Ã¢Å¡Â Ã¯Â¸Â Clipboard error: {str(e)}")
        return

    if command == "/startup":
        try:
            result = execute_command("wmic startup get Caption, Command")
            bot.send_message(message.chat.id, f"Ã°Å¸Å¡â‚¬ ÃŽâ€¢ÃŽÂºÃŽÂºÃŽÂ¯ÃŽÂ½ÃŽÂ·ÃÆ’ÃŽÂ·:\n{result}")
        except:
            pass
        return

# -- LAUNCH EVERYTHING --
threading.Thread(target=bot.polling, daemon=True).start()
threading.Thread(target=tray, daemon=True).start()
threading.Thread(target=watch_network, daemon=True).start()
threading.Thread(target=check_inactivity, daemon=True).start()
threading.Thread(target=recognize_speech, daemon=True).start()

while True:
    time.sleep(1)
