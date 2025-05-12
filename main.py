from flask import Flask, request
import requests
import threading
import time
from config import BOT_TOKEN, WEBHOOK_URL, ADMIN_IDS, CHANNEL_TAG, PING_INTERVAL
from utils import gen_code, save_file, get_files, increase_downloads, get_download_count,
    add_required_channel, remove_required_channel, list_required_channels, check_user_membership

app = Flask(__name__)
URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
users = {}
pinging = True

def send(method, data):
    response = requests.post(f"{URL}/{method}", json=data).json()
    print(f"Response from {method}: {response}")
    return response

def delete(chat_id, message_id):
    send("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

def ping():
    while pinging:
        try:
            requests.get(WEBHOOK_URL)
        except:
            pass
        time.sleep(PING_INTERVAL)

threading.Thread(target=ping, daemon=True).start()

@app.route("/")
def index():
    return "Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json()

    if "message" in update:
        msg = update["message"]
        uid = msg["from"]["id"]
        cid = msg["chat"]["id"]
        mid = msg["message_id"]
        text = msg.get("text", "")
        state = users.get(uid, {})

        if text.startswith("/start"):
            args = text.split(" ")
            if len(args) > 1:
                code = args[1]
                async def handle_start():
                    not_joined = await check_user_membership(requests, uid)
                    if not_joined:
                        buttons = [[{"text": ch, "url": f"https://t.me/{ch}"}] for ch in not_joined]
                        buttons.append([{"text": "عضو شدم✅", "callback_data": f"check:{code}"}])
                        send("sendMessage", {
                            "chat_id": cid,
                            "text": "قبل از دریافت فایل، لطفاً در کانال‌های زیر عضو شو:",
                            "reply_markup": {"inline_keyboard": buttons}
                        })
                    else:
                        files = get_files(code)
                        for f in files:
                            send("sendVideo", {"chat_id": cid, "video": f})
                        increase_downloads(code)
                import asyncio
                asyncio.run(handle_start())
            else:
                send("sendMessage", {"chat_id": cid, "text": "سلام خوش اومدی عزیزم واسه دریافت فایل مد نظرت از کانال @hottof روی دکمه مشاهده بزن ♥️"})

        elif text == "/panel" and uid in ADMIN_IDS:
            kb = {"keyboard": [[{"text": "🔞سوپر"}], [{"text": "🖼پست"}], [{"text": "⚙️تنظیمات"}]], "resize_keyboard": True}
            send("sendMessage", {"chat_id": cid, "text": "سلام آقا مدیر 🔱", "reply_markup": kb})

        elif text == "⚙️تنظیمات" and uid in ADMIN_IDS:
            users[uid] = {"step": "settings"}
            kb = {"keyboard": [[{"text": "➕افزودن کانال"}], [{"text": "➖حذف کانال"}], [{"text": "📋مشاهده کانال‌ها"}], [{"text": "بازگشت"}]], "resize_keyboard": True}
            send("sendMessage", {"chat_id": cid, "text": "چیکار میخوای بکنی؟", "reply_markup": kb})

        elif text == "➕افزودن کانال" and state.get("step") == "settings":
            users[uid]["step"] = "adding_channel"
            send("sendMessage", {"chat_id": cid, "text": "آیدی کانال رو بدون @ بفرست و یادت نره منو ادمین کنی."})

        elif state.get("step") == "adding_channel":
            add_required_channel(text)
            users[uid] = {"step": "settings"}
            send("sendMessage", {"chat_id": cid, "text": "✅ کانال اضافه شد و برگشتیم به تنظیمات"})

        elif text == "➖حذف کانال" and state.get("step") == "settings":
            users[uid]["step"] = "removing_channel"
            send("sendMessage", {"chat_id": cid, "text": "آیدی کانالی که میخوای حذف شه رو بدون @ بفرست."})

        elif state.get("step") == "removing_channel":
            remove_required_channel(text)
            users[uid] = {"step": "settings"}
            send("sendMessage", {"chat_id": cid, "text": "❌ کانال حذف شد و برگشتیم به تنظیمات"})

        elif text == "📋مشاهده کانال‌ها" and state.get("step") == "settings":
            channels = list_required_channels()
            ch_text = "\n".join(channels) if channels else "هیچ کانالی ثبت نشده."
            send("sendMessage", {"chat_id": cid, "text": ch_text})

        elif text == "بازگشت":
            users.pop(uid, None)
            send("sendMessage", {"chat_id": cid, "text": "برگشتیم به پنل.", "reply_markup": {"keyboard": [[{"text": "🔞سوپر"}], [{"text": "🖼پست"}], [{"text": "⚙️تنظیمات"}]], "resize_keyboard": True}})

        elif text == "🔞سوپر" and uid in ADMIN_IDS:
            users[uid] = {"step": "awaiting_videos", "videos": []}
            send("sendMessage", {"chat_id": cid, "text": "تا 10 ویدیو بفرست (یکی یکی). وقتی تموم شد، بگو \"تمام\"."})

        elif state.get("step") == "awaiting_videos" and "video" in msg:
            users[uid]["videos"].append(msg["video"]["file_id"])
            send("sendMessage", {"chat_id": cid, "text": f"ویدیو دریافت شد ({len(users[uid]['videos'])}/10)"})

        elif state.get("step") == "awaiting_videos" and text == "تمام":
            if not users[uid]["videos"]:
                send("sendMessage", {"chat_id": cid, "text": "هیچ ویدیویی دریافت نشد."})
            else:
                users[uid]["step"] = "awaiting_caption"
                send("sendMessage", {"chat_id": cid, "text": "کپشن رو بفرست"})

elif text == "تنظیمات" and uid in ADMIN_IDS:
            kb = {
                "keyboard": [
                    [{"text": "➕افزودن کانال"}],
                    [{"text": "➖حذف کانال"}],
                    [{"text": "📋مشاهده کانال ها"}],
                    [{"text": "🔙بازگشت"}]
                ],
                "resize_keyboard": True
            }
            users[uid] = {"step": "settings_menu"}
            send("sendMessage", {"chat_id": cid, "text": "چیکار میخوای بکنی؟", "reply_markup": kb})

        elif text == "➕افزودن کانال" and state.get("step") == "settings_menu":
            users[uid]["step"] = "awaiting_channel_add"
            send("sendMessage", {"chat_id": cid, "text": "آیدی کانال رو بدون @ بفرست و منو ادمین کن حتماً"})

        elif state.get("step") == "awaiting_channel_add":
            add_required_channel(text)
            users.pop(uid)
            send("sendMessage", {"chat_id": cid, "text": "کانال با موفقیت اضافه شد ✅"})

        elif text == "➖حذف کانال" and state.get("step") == "settings_menu":
            users[uid]["step"] = "awaiting_channel_remove"
            send("sendMessage", {"chat_id": cid, "text": "آیدی کانال رو بدون @ بفرست که حذف کنم"})

        elif state.get("step") == "awaiting_channel_remove":
            remove_required_channel(text)
            users.pop(uid)
            send("sendMessage", {"chat_id": cid, "text": "کانال حذف شد ✅"})

        elif text == "📋مشاهده کانال ها" and state.get("step") == "settings_menu":
            chs = list_required_channels()
            txt = "\n".join([f"- @{ch}" for ch in chs]) if chs else "هیچ کانالی تنظیم نشده"
            send("sendMessage", {"chat_id": cid, "text": txt})

        elif text == "🔙بازگشت" and state.get("step") == "settings_menu":
            users.pop(uid)
            kb = {"keyboard": [[{"text": "🔞سوپر"}], [{"text": "🖼پست"}], [{"text": "تنظیمات"}]], "resize_keyboard": True}
            send("sendMessage", {"chat_id": cid, "text": "بازگشتیم به پنل اصلی", "reply_markup": kb})

    return "ok"

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
