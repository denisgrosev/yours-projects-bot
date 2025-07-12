import os
import sys
import asyncio
import aiohttp
import datetime
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.payments import GetStarGiftsRequest

# Получение из переменных окружения
api_id = int(os.getenv("GIFT_API_ID"))
api_hash = os.getenv("GIFT_API_HASH")
GIFT_BOT_TOKEN = os.getenv("GIFT_BOT_TOKEN")

session_dir = "/app/data/files212/GIFT"
session_file = os.path.join(session_dir, "session.txt")
CHECK_INTERVAL = 3  # секунда

YOUR_TELEGRAM_USER_IDS = [5236886477, 1463991582]
BOT_API_URL = f"https://api.telegram.org/bot{GIFT_BOT_TOKEN}/sendMessage"

# --- Логирование всего вывода ---
def get_log_file_path():
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    return os.path.join(session_dir, f"log_{timestamp}.txt")

class TeeStream:
    def __init__(self, *streams):
        self.streams = streams
    def write(self, data):
        for s in self.streams:
            try:
                s.write(data)
                s.flush()
            except Exception:
                pass
    def flush(self):
        for s in self.streams:
            try:
                s.flush()
            except Exception:
                pass

if not os.path.exists(session_dir):
    os.makedirs(session_dir, exist_ok=True)

log_file_path = get_log_file_path()
log_file = open(log_file_path, "a", encoding="utf-8")
sys.stdout = TeeStream(sys.stdout, log_file)
sys.stderr = TeeStream(sys.stderr, log_file)
print(f"📝 Логирование в файл: {log_file_path}")

async def notify_user(message):
    print("📤 Отправка уведомления пользователям...")
    try:
        async with aiohttp.ClientSession() as session:
            for user_id in YOUR_TELEGRAM_USER_IDS:
                payload = {
                    "chat_id": user_id,
                    "text": message
                }
                async with session.post(BOT_API_URL, data=payload) as resp:
                    if resp.status == 200:
                        print(f"✅ Уведомление отправлено: {user_id}")
                    else:
                        print(f"⚠️ Не удалось отправить {user_id}, код: {resp.status}")
    except Exception as e:
        print("❌ Ошибка при отправке уведомлений:", e)

if os.path.exists(session_file):
    print("📂 Найден файл сессии, загружаем...")
    with open(session_file, "r") as f:
        session_str = f.read().strip()
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
else:
    print("📁 Файл сессии не найден, создаем новую сессию...")
    client = TelegramClient(StringSession(), api_id, api_hash)

async def get_limited_gifts(client):
    print("🔎 Проверяем наличие лимитированных подарков...")
    try:
        result = await client(GetStarGiftsRequest(hash=0))
        gifts = []
        for gift in getattr(result, "gifts", []):
            if getattr(gift, "limited", False) and not getattr(gift, "sold_out", False):
                remains = getattr(gift, "availability_remains", 0)
                title = getattr(gift, "title", None) or getattr(gift, "alt", None) or f"ID: {gift.id}"
                gifts.append({
                    "id": gift.id,
                    "title": title,
                    "stars": getattr(gift, "stars", 0),
                    "remains": remains,
                })
        print(f"🎁 Найдено {len(gifts)} лимитированных подарков.")
        return sorted(gifts, key=lambda g: -g["stars"])
    except Exception as e:
        print("❌ Ошибка при получении лимитированных подарков:", e)
        return []

async def main():
    if not os.path.exists(session_file):
        print("🚀 Запуск новой сессии...")
        await client.start()
        with open(session_file, "w") as f:
            f.write(client.session.save())
        print("✅ Сессия сохранена.")
    else:
        print("🔑 Авторизация с использованием существующей сессии...")
        await client.start()
        print("✅ Сессия загружена.")

    message = "НОВЫЕ ПОДАРКИ🎁🎁🎁 ААААА СРОЧНО🎁⚠️ ААААААААА ⚠️⚠️⚠️КАПЕЦ ДУОЛИНГО ААААА 🎁🎁🎁🎁🎁ПОДАРКИ ПОДАРКИ⚠️⚠️⚠️⚠️⚠️⚠️⚠"

    print("🔁 Переход в режим постоянного мониторинга...")
    gifts_were = False
    while True:
        try:
            gifts = await get_limited_gifts(client)
            has_gifts = bool(gifts)
            if has_gifts and not gifts_were:
                print("📣 Обнаружены новые лимитированные подарки!")

                # 🔔 Рассылка 5 мгновенных уведомлений
                for i in range(5):
                    print(f"📨 Уведомление {i + 1}/5")
                    await notify_user(message)

                # ⏱️ 15 уведомлений с задержкой
                for i in range(15):
                    await asyncio.sleep(1)
                    print(f"⏱️ Уведомление с задержкой {i + 1}/15")
                    await notify_user(message)

            elif has_gifts:
                print("🟢 Подарки есть, но уже были замечены ранее.")
            else:
                print("⚪ Лимитированных подарков нет.")

            gifts_were = has_gifts
        except Exception as e:
            print("❌ Ошибка во время мониторинга:", e)
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    # Проверяем, что все нужные переменные окружения определены
    for var in ("GIFT_API_ID", "GIFT_API_HASH", "GIFT_BOT_TOKEN"):
        if not os.getenv(var):
            raise RuntimeError(f"Не установлена переменная окружения: {var}")
    asyncio.run(main())