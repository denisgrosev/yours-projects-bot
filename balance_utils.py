import os
import json
import asyncio
from telegram import Bot

# Жёстко задаём путь к файлу баланса
BALANCE_FILE = "/app/data/files212/user_balances.json"

# Жёстко задаём токен ТГ-бота (НЕ рекомендуется для публичного кода!)
BOT_TOKEN = "7819985767:AAG130I3AVmnskfJOSL95q7yga69VMiyeDU"

def load_balances():
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_balances(balances):
    os.makedirs(os.path.dirname(BALANCE_FILE), exist_ok=True)
    with open(BALANCE_FILE, "w", encoding="utf-8") as f:
        json.dump(balances, f, ensure_ascii=False, indent=2)

def notify_user(user_id, message):
    """
    Универсальная функция для отправки уведомлений.
    Работает и с python-telegram-bot 13.x (sync), и с 20.x+ (async).
    """
    try:
        bot = Bot(token=BOT_TOKEN)
        send_msg = bot.send_message
        if asyncio.iscoroutinefunction(send_msg):
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                asyncio.create_task(send_msg(chat_id=user_id, text=message))
            else:
                asyncio.run(send_msg(chat_id=user_id, text=message))
        else:
            send_msg(chat_id=user_id, text=message)
    except Exception as e:
        print(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")

def get_referrer_id(user_id):
    balances = load_balances()
    user_id_str = str(user_id)
    user = balances.get(user_id_str)
    return user.get("referrer_id") if user else None

def update_user_info(user_id, username, referrer_id=None):
    balances = load_balances()
    user_id_str = str(user_id)
    changed = False
    if user_id_str not in balances or not isinstance(balances[user_id_str], dict):
        balances[user_id_str] = {
            "balance": 0,
            "ref_balance": 0,
            "username": username,
            "referrer_id": referrer_id
        }
        changed = True
    else:
        balances[user_id_str]["username"] = username
        # referrer_id можно прописать только при регистрации!
        if referrer_id and not balances[user_id_str].get("referrer_id"):
            balances[user_id_str]["referrer_id"] = referrer_id
            changed = True
    if changed:
        save_balances(balances)

def find_user_id_by_username(username):
    balances = load_balances()
    username = username.lower()
    if username.startswith("@"):
        username = username[1:]
    for user_id, info in balances.items():
        db_username = info.get("username")
        if isinstance(db_username, str) and db_username.lower() == username:
            return int(user_id)
    return None

def get_user_balance(user_id):
    balances = load_balances()
    user_id_str = str(user_id)
    if user_id_str not in balances or not isinstance(balances[user_id_str], dict):
        balances[user_id_str] = {"balance": 0, "ref_balance": 0, "username": None}
        save_balances(balances)
    return balances[user_id_str].get("balance", 0)

def set_user_balance(user_id, amount, admin_action=False, admin_id=None):
    balances = load_balances()
    user_id_str = str(user_id)
    before = balances.get(user_id_str, {}).get("balance", 0)
    if user_id_str not in balances or not isinstance(balances[user_id_str], dict):
        balances[user_id_str] = {"balance": float(amount), "ref_balance": 0, "username": None}
    else:
        balances[user_id_str]["balance"] = float(amount)
    save_balances(balances)
    if admin_action:
        msg = f"⚠️ Ваш баланс был установлен администратором на {float(amount)}₽ (было: {before}₽)."
    else:
        msg = f"Ваш баланс теперь: {float(amount)}₽."
    notify_user(user_id, msg)
    if admin_id:
        msg_admin = f"Вы установили пользователю {user_id} баланс на {float(amount)}₽ (было: {before}₽)."
        notify_user(admin_id, msg_admin)

def add_user_balance(user_id, amount, source="", admin_id=None):
    balances = load_balances()
    user_id_str = str(user_id)
    before = balances.get(user_id_str, {}).get("balance", 0)
    if user_id_str not in balances or not isinstance(balances[user_id_str], dict):
        balances[user_id_str] = {"balance": float(amount), "ref_balance": 0, "username": None}
        after = float(amount)
    else:
        balances[user_id_str]["balance"] = balances[user_id_str].get("balance", 0) + float(amount)
        after = balances[user_id_str]["balance"]
    save_balances(balances)
    msg = f"Ваш баланс пополнен на {float(amount)}₽. Текущий баланс: {after}₽"
    if source:
        msg += f"\nИсточник: {source}"
    notify_user(user_id, msg)
    if admin_id:
        msg_admin = f"Вы пополнили баланс пользователя {user_id} на {float(amount)}₽. Новый баланс: {after}₽"
        notify_user(admin_id, msg_admin)

def deduct_user_balance(user_id, amount, reason="", admin_id=None):
    balances = load_balances()
    user_id_str = str(user_id)
    if user_id_str not in balances or not isinstance(balances[user_id_str], dict):
        balances[user_id_str] = {"balance": 0, "ref_balance": 0, "username": None}
        save_balances(balances)
        return False
    current = balances[user_id_str].get("balance", 0)
    if current >= float(amount):
        balances[user_id_str]["balance"] = current - float(amount)
        save_balances(balances)
        msg = f"С вашего баланса списано {float(amount)}₽. Остаток: {balances[user_id_str]['balance']}₽"
        if reason:
            msg += f"\nПричина: {reason}"
        notify_user(user_id, msg)
        if admin_id:
            msg_admin = f"Вы списали у пользователя {user_id} {float(amount)}₽. Остаток: {balances[user_id_str]['balance']}₽"
            notify_user(admin_id, msg_admin)
        return True
    return False

def minus_user_balance(user_id, amount, reason="", admin_id=None):
    balances = load_balances()
    user_id_str = str(user_id)
    before = balances.get(user_id_str, {}).get("balance", 0)
    if user_id_str not in balances or not isinstance(balances[user_id_str], dict):
        balances[user_id_str] = {"balance": -float(amount), "ref_balance": 0, "username": None}
        after = -float(amount)
    else:
        balances[user_id_str]["balance"] = balances[user_id_str].get("balance", 0) - float(amount)
        after = balances[user_id_str]["balance"]
    save_balances(balances)
    msg = f"Ваш баланс уменьшен на {float(amount)}₽. Текущий баланс: {after}₽"
    if after < 0:
        msg += "\nВнимание! Ваш баланс отрицательный."
    if reason:
        msg += f"\nПричина: {reason}"
    notify_user(user_id, msg)
    if admin_id:
        msg_admin = f"Вы уменьшили баланс пользователя {user_id} на {float(amount)}₽. Новый баланс: {after}₽"
        notify_user(admin_id, msg_admin)

def get_ref_balance(user_id):
    balances = load_balances()
    user_id_str = str(user_id)
    return balances.get(user_id_str, {}).get("ref_balance", 0)

def set_ref_balance(user_id, value, admin_action=False, admin_id=None):
    balances = load_balances()
    user_id_str = str(user_id)
    before = balances.get(user_id_str, {}).get("ref_balance", 0)
    if user_id_str in balances:
        balances[user_id_str]["ref_balance"] = float(value)
        save_balances(balances)
        if admin_action:
            msg = f"⚠️ Ваш реферальный баланс был установлен администратором на {float(value)}₽ (было: {before}₽)."
        else:
            msg = f"Ваш реферальный баланс теперь: {float(value)}₽."
        notify_user(user_id, msg)
        if admin_id:
            msg_admin = f"Вы установили реферальный баланс пользователя {user_id} на {float(value)}₽ (было: {before}₽)."
            notify_user(admin_id, msg_admin)

def add_ref_balance(user_id, amount, source="", admin_id=None):
    balances = load_balances()
    user_id_str = str(user_id)
    before = balances.get(user_id_str, {}).get("ref_balance", 0)
    after = before
    if user_id_str in balances:
        balances[user_id_str]["ref_balance"] = balances[user_id_str].get("ref_balance", 0) + float(amount)
        after = balances[user_id_str]["ref_balance"]
        save_balances(balances)
        msg = f"Ваш реферальный баланс пополнен на {float(amount)}₽. Текущий реф. баланс: {after}₽"
        if source:
            msg += f"\nИсточник: {source}"
        notify_user(user_id, msg)
        if admin_id:
            msg_admin = f"Вы пополнили реферальный баланс пользователя {user_id} на {float(amount)}₽. Новый реф. баланс: {after}₽"
            notify_user(admin_id, msg_admin)

def process_referral_bonus(user_id, amount):
    balances = load_balances()
    user_id_str = str(user_id)
    user = balances.get(user_id_str)
    if user and user.get("referrer_id"):
        referrer_id = str(user["referrer_id"])
        bonus = round(float(amount) * 0.2, 2)
        if referrer_id in balances:
            before = balances[referrer_id].get("ref_balance", 0)
            balances[referrer_id]["ref_balance"] = balances[referrer_id].get("ref_balance", 0) + bonus
            after = balances[referrer_id]["ref_balance"]
            save_balances(balances)
            msg = (
                f"Вам начислен реферальный бонус: {bonus}₽!\n"
                f"Теперь ваш реферальный баланс: {after}₽"
            )
            notify_user(referrer_id, msg)
            return bonus, referrer_id
    return 0, None
