import requests
import time
import json
import sqlite3

TOKEN = "8904576909:AAF0HbgrPppu4GlFGdRVTwgSMuShYlZTA9I"
ADMIN_ID = 8581730908

URL = f"https://api.telegram.org/bot{TOKEN}/"

# ================= DATABASE =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    pubg TEXT,
    uc TEXT,
    price TEXT,
    status TEXT
)
""")
conn.commit()

user_data = {}
last_update_id = 0

prices = {
    "60": "13000",
    "120": "26000",
    "180": "38000",
    "325": "62000",
    "660": "125000",
    "720": "137000",
    "985": "185000",
    "1320": "245000",
    "1800": "299000",
    "2125": "360000",
    "3120": "540000"
}

CARD = "💳 KARTA: 5614 6887 1234 1345"

# ================= SEND =================
def send(chat_id, text):
    requests.post(URL + "sendMessage", data={"chat_id": chat_id, "text": text})

def get_updates():
    global last_update_id
    r = requests.get(URL + f"getUpdates?offset={last_update_id + 1}")
    return r.json()

# ================= LOOP =================
while True:
    data = get_updates()

    if "result" in data:

        for u in data["result"]:
            last_update_id = u["update_id"]

            # ================= TEXT =================
            if "message" in u and "text" in u["message"]:

                msg = u["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text")

                if not text:
                    continue

                if text.startswith("/start"):
                    send(chat_id, "🛒 BOT ISHLAYAPTI\n/order yozing")

                elif text == "/order":
                    user_data[chat_id] = {"step": 1}
                    send(chat_id, "🎮 PUBG ID yuboring")

                elif chat_id in user_data:

                    # STEP 1
                    if user_data[chat_id]["step"] == 1:
                        user_data[chat_id]["pubg"] = text
                        user_data[chat_id]["step"] = 2

                        send(chat_id,
"""🪙 UC TANLANG:

60 | 120 | 180
325 | 660 | 720
985 | 1320 | 1800
2125 | 3120
""")

                    # STEP 2
                    elif user_data[chat_id]["step"] == 2:

                        if text not in prices:
                            send(chat_id, "❗ UC noto‘g‘ri")
                            continue

                        user_data[chat_id]["uc"] = text
                        user_data[chat_id]["price"] = prices[text]
                        user_data[chat_id]["step"] = 3

                        send(chat_id,
f"""🆕 BUYURTMA

🎮 PUBG ID: {user_data[chat_id]["pubg"]}
🪙 UC: {text}
💰 {prices[text]}

{CARD}

📸 Chek yuboring
""")

            # ================= PHOTO =================
            if "message" in u and "photo" in u["message"]:

                msg = u["message"]
                chat_id = msg["chat"]["id"]

                if chat_id not in user_data or user_data[chat_id]["step"] != 3:
                    send(chat_id, "❗ Avval /order qiling")
                    continue

                photo_id = msg["photo"][-1]["file_id"]

                pubg = user_data[chat_id]["pubg"]
                uc = user_data[chat_id]["uc"]
                price = user_data[chat_id]["price"]

                # ================= SAVE DB =================
                cur.execute("""
                INSERT INTO orders (chat_id, pubg, uc, price, status)
                VALUES (?, ?, ?, ?, ?)
                """, (chat_id, pubg, uc, price, "pending"))

                conn.commit()

                oid = cur.lastrowid

                send(chat_id, "✅ Buyurtma qabul qilindi!")

                requests.post(URL + "sendPhoto", data={
                    "chat_id": ADMIN_ID,
                    "photo": photo_id,
                    "caption": f"""🆕 ORDER #{oid}

🎮 PUBG ID: {pubg}
🪙 UC: {uc}
💰 {price}

✔ Yopish: done_{oid}
"""
                })

                del user_data[chat_id]

            # ================= ADMIN DONE =================
            if "message" in u and "text" in u["message"]:

                msg = u["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text")

                if chat_id == ADMIN_ID and text and text.startswith("done_"):

                    oid = text.split("_")[1]

                    cur.execute("SELECT chat_id FROM orders WHERE id=?", (oid,))
                    row = cur.fetchone()

                    if row:
                        user = row[0]

                        send(user, "🎉 UC tushdi! Xaridingiz uchun rahmat 💙")

                        cur.execute("UPDATE orders SET status=? WHERE id=?", ("done", oid))
                        conn.commit()

                        send(ADMIN_ID, f"✅ Order #{oid} yopildi")

    time.sleep(1)
