import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import time
import threading
from datetime import datetime
import telebot
from flask import Flask, request, render_template, jsonify
from PIL import Image, ImageTk

# Telegram Bot API Key
TELEGRAM_API_KEY = "Ваш API bota"
bot = telebot.TeleBot(TELEGRAM_API_KEY)

# Flask web server setup
app = Flask(__name__)

# Global variables
chat_id = None
file_content = []
message_delay = 1  # Задержка между сообщениями
background_color = "#2b2b2b"
is_active = False  # Указывает, активирован ли бот в чате

# Telegram bot setup
@bot.message_handler(commands=["start"])
def handle_start(message):
    global chat_id, is_active
    chat_id = message.chat.id
    is_active = True  # Активируем бота для этого чата
    bot.send_message(chat_id, "Бот активирован! Теперь вы можете отправлять сообщения через GUI или веб-интерфейс.")
    print(f"Бот активирован для чата ID: {chat_id}")

@bot.message_handler(commands=["help"])
def handle_help(message):
    bot.send_message(
        message.chat.id,
        "Команды:\n"
        "/start - Активировать бота для этого чата\n"
        "/help - Показать это сообщение"
    )

# Flask routes
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    global file_content
    try:
        file = request.files["file"]
        if file:
            file_content = file.read().decode("utf-8").splitlines()
            return jsonify({"status": "success", "message": "Файл успешно загружен!"})
        return jsonify({"status": "error", "message": "Не выбран файл!"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка загрузки файла: {e}"})

@app.route("/send", methods=["POST"])
def web_send_messages():
    global file_content, message_delay, chat_id, is_active
    if not is_active:
        return jsonify({"status": "error", "message": "Бот не активирован. Напишите /start в чате Telegram."})
    if not chat_id:
        return jsonify({"status": "error", "message": "Чат ID отсутствует. Добавьте бота в группу!"})
    if not file_content:
        return jsonify({"status": "error", "message": "Нет содержимого файла для отправки."})

    threading.Thread(target=send_messages, args=(file_content, message_delay), daemon=True).start()
    return jsonify({"status": "success", "message": "Сообщения отправляются."})

def send_messages(content, delay=1):
    global chat_id
    if chat_id:
        try:
            for line in content:
                bot.send_message(chat_id, line.strip())
                time.sleep(delay)
        except Exception as e:
            print(f"Ошибка отправки сообщений: {e}")

# Flask server thread
def run_flask():
    app.run(port=5000, debug=False, use_reloader=False)

threading.Thread(target=run_flask, daemon=True).start()

# Tkinter GUI
class VisualTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Управление Telegram ботом")
        self.root.geometry("800x600")
        self.root.configure(bg=background_color)

        self.timer_running = False
        self.file_content = []
        self.chat_id = chat_id

        # Выбор файла
        ttk.Label(root, text="Выберите файл TXT:", foreground="white", background=background_color).pack(pady=10)
        ttk.Button(root, text="Выбрать файл", command=self.choose_file).pack(pady=5)

        # Задержка сообщений
        ttk.Label(root, text="Настройте задержку между сообщениями (секунды):", foreground="white", background=background_color).pack(pady=10)
        self.delay_var = tk.IntVar(value=1)
        ttk.Scale(root, from_=1, to=10, variable=self.delay_var, orient="horizontal").pack(pady=5)

        # Кнопка отправки
        ttk.Button(root, text="Отправить сообщения", command=self.send_messages).pack(pady=5)

        # Фон
        ttk.Button(root, text="Изменить цвет фона", command=self.change_background).pack(pady=5)

    def choose_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Текстовые файлы", "*.txt")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as file:
                self.file_content = file.readlines()
            messagebox.showinfo("Успешно", f"Файл {file_path} загружен!")

    def send_messages(self):
        global chat_id, is_active
        if not is_active:
            messagebox.showerror("Ошибка", "Бот не активирован в чате. Напишите /start в Telegram чате.")
            return
        if not chat_id:
            messagebox.showerror("Ошибка", "Чат ID отсутствует. Добавьте бота в группу!")
            return
        if not self.file_content:
            messagebox.showerror("Ошибка", "Сначала загрузите файл TXT!")
            return
        delay = self.delay_var.get()
        threading.Thread(target=send_messages, args=(self.file_content, delay), daemon=True).start()

    def change_background(self):
        global background_color
        color = colorchooser.askcolor()[1]
        if color:
            background_color = color
            self.root.configure(bg=color)

# Start bot polling
def run_bot():
    while True:
        try:
            bot.remove_webhook()
            bot.polling(non_stop=True, interval=0)
        except Exception as e:
            print(f"Ошибка polling: {e}")
            time.sleep(5)

threading.Thread(target=run_bot, daemon=True).start()

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = VisualTimerApp(root)
    root.mainloop()
