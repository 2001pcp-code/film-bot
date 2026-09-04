import os
import json
import requests
import time
from threading import Thread
from flask import Flask

app = Flask(__name__)
TOKEN = "8815980987:AAGFFRoW6SOTsXCDnjhD1ybwwvFmQJZ1OuI"
URL = f"https://api.telegram.org/bot{TOKEN}"
DATA_FILE = "films.json"

def load_films():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_films(films):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(films, f, ensure_ascii=False, indent=2)

def send_message(chat_id, text):
    requests.get(URL + "/sendMessage", params={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})

def get_updates(offset=None):
    params = {"timeout": 30, "offset": offset}
    response = requests.get(URL + "/getUpdates", params=params)
    return response.json()["result"]

def bot_loop():
    films = load_films()
    offset = 0
    print("🤖 Бот запущен...")
    while True:
        try:
            updates = get_updates(offset)
            for update in updates:
                message = update.get("message")
                if not message:
                    continue
                chat_id = message["chat"]["id"]
                text = message.get("text", "")
                username = message["chat"].get("first_name", "Кто-то")

                if text == "/start":
                    send_message(chat_id, f"Привет, {username}! 👋\nЭто общий бот для всей семьи.\n\n📌 Отправь ссылку или сообщение — все увидят!\n/list — показать всё\n/clear — очистить общий список")
                elif text == "/list":
                    if not films:
                        send_message(chat_id, "📭 Пока нет общих записей.")
                    else:
                        msg = "📋 <b>Общая лента:</b>\n\n"
                        for i, f in enumerate(films, 1):
                            msg += f"{i}. <b>{f['title'][:40]}</b>\n   👤 {f['added_by']}\n   🔗 {f['link']}\n"
                            if f.get('review'):
                                msg += f"   📝 {f['review'][:60]}\n"
                            msg += "\n"
                        send_message(chat_id, msg)
                elif text == "/clear":
                    films.clear()
                    save_films(films)
                    send_message(chat_id, "🗑️ Общий список очищен.")
                else:
                    if "http" in text or len(text) > 10:
                        lines = text.split("\n")
                        link = ""
                        review = ""
                        title = "Запись"
                        for line in lines:
                            if "http" in line:
                                link = line.strip()
                            elif line.strip():
                                if not title or title == "Запись":
                                    title = line.strip()
                                else:
                                    review += line.strip() + " "
                        if not link and "http" not in text:
                            link = "📝 Без ссылки"
                            title = text[:40]
                        films.append({"title": title, "link": link, "review": review.strip() or "Без рецензии", "added_by": username})
                        save_films(films)
                        send_message(chat_id, f"✅ Сохранено в общую ленту!\n\n📌 {title}\n👤 Отправил: {username}\nВсего записей: {len(films)}")
                    else:
                        send_message(chat_id, "📩 Отправь сообщение или ссылку — я сохраню в общую ленту для всех.\n\n/list — показать всё\n/clear — очистить")
                offset = update["update_id"] + 1
        except Exception as e:
            print("Ошибка:", e)
        time.sleep(1)

@app.route('/')
def home():
    return "🤖 Бот работает!"

@app.route('/health')
def health():
    return "OK"

if __name__ == "__main__":
    thread = Thread(target=bot_loop)
    thread.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
