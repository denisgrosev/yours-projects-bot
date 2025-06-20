import os
import json
import asyncio
import datetime
from telegram import Bot

# Жёстко задаём путь к файлу баланса
BALANCE_FILE = "/app/data/files212/balance_utils/user_balances.json"
LOG_DIR = "/app/data/files212/balance_utils/log"

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def log(message):
    os.makedirs(LOG_DIR, exist_ok=True)
    now = datetime.datetime.now()
    log_filename = now.strftime("log_%Y-%m-%d_%H-%M-%S.txt")
    log_path = os.path.join(LOG_DIR, log_filename)
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S.%f")
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")

def load_balances():
    log("Вызван load_balances()")
    if os.path.exists(BALANCE_FILE):
        try:
            with open(BALANCE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                log(f"Успешно загружен баланс из {BALANCE_FILE}")
                return data
        except Exception as e:
            log(f"Ошибка чтения {BALANCE_FILE}: {e}")
            return {}
    log(f"Файл {BALANCE_FILE} не найден, возвращён пустой словарь")
    return {}

def save_balances(balances):
    log(f"Вызван save_balances(). Сохраняем данные: {balances}")
    try:
        os.makedirs(os.path.dirname(BALANCE_FILE), exist_ok=True)
        with open(BALANCE_FILE, "w", encoding="utf-8") as f:
            json.dump(balances, f, ensure_ascii=False, indent=2)
        log(f"Данные успешно сохранены в {BALANCE_FILE}")
    except Exception as e:
        log(f"Ошибка при сохранении {BALANCE_FILE}: {e}")

def notify_user(user_id, message):
    log(f"notify_user: user_id={user_id}, message={message}")
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
                log(f"Отправлено асинхронное сообщение пользователю {user_id}")
            else:
                asyncio.run(send_msg(chat_id=user_id, text=message))
                log(f"Отправлено асинхронное сообщение (через run) пользователю {user_id}")
        else:
            send_msg(chat_id=user_id, text=message)
            log(f"Отправлено синхронное сообщение пользователю {user_id}")
    except Exception as e:
        log(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")
        print(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")

def get_referrer_id(user_id):
    log(f"Вызван get_referrer_id(user_id={user_id})")
    balances = load_balances()
    user_id_str = str(user_id)
    user = balances.get(user_id_str)
    ref_id = user.get("referrer_id") if user else None
    log(f"get_referrer_id: найден referrer_id={ref_id}")
    return ref_id

def update_user_info(user_id, username, referrer_id=None):
    log(f"Вызван update_user_info(user_id={user_id}, username={username}, referrer_id={referrer_id})")
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
        log(f"Зарегистрирован новый пользователь {user_id_str} с username={username} и referrer_id={referrer_id}")
    else:
        balances[user_id_str]["username"] = username
        if referrer_id and not balances[user_id_str].get("referrer_id"):
            balances[user_id_str]["referrer_id"] = referrer_id
            changed = True
            log(f"Добавлен referrer_id={referrer_id} для пользователя {user_id_str}")
    if changed:
        save_balances(balances)
        log(f"Данные пользователя {user_id_str} обновлены: {balances[user_id_str]}")

def find_user_id_by_username(username):
    log(f"Вызван find_user_id_by_username(username={username})")
    balances = load_balances()
    username_search = username.lower()
    if username_search.startswith("@"):
        username_search = username_search[1:]
    for user_id, info in balances.items():
        db_username = info.get("username")
        if isinstance(db_username, str) and db_username.lower() == username_search:
            log(f"Найден user_id={user_id} по username={username}")
            return int(user_id)
    log(f"Пользователь с username={username} не найден")
    return None

def get_user_balance(user_id):
    log(f"Вызван get_user_balance(user_id={user_id})")
    balances = load_balances()
    user_id_str = str(user_id)
    if user_id_str not in balances or not isinstance(balances[user_id_str], dict):
        balances[user_id_str] = {"balance": 0, "ref_balance": 0, "username": None}
        save_balances(balances)
        log(f"Пользователь {user_id_str} не найден, создан с нулевым балансом")
    balance = balances[user_id_str].get("balance", 0)
    log(f"Текущий баланс пользователя {user_id_str}: {balance}")
    return balance

def set_user_balance(user_id, amount, admin_action=False, admin_id=None):
    log(f"Вызван set_user_balance(user_id={user_id}, amount={amount}, admin_action={admin_action}, admin_id={admin_id})")
    balances = load_balances()
    user_id_str = str(user_id)
    before = balances.get(user_id_str, {}).get("balance", 0)
    if user_id_str not in balances or not isinstance(balances[user_id_str], dict):
        balances[user_id_str] = {"balance": float(amount), "ref_balance": 0, "username": None}
        log(f"Создан новый пользователь {user_id_str} с балансом {amount}")
    else:
        balances[user_id_str]["balance"] = float(amount)
        log(f"Изменён баланс пользователя {user_id_str}: было {before}, стало {amount}")
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
    log(f"Вызван add_user_balance(user_id={user_id}, amount={amount}, source={source}, admin_id={admin_id})")
    balances = load_balances()
    user_id_str = str(user_id)
    before = balances.get(user_id_str, {}).get("balance", 0)
    if user_id_str not in balances or not isinstance(balances[user_id_str], dict):
        balances[user_id_str] = {"balance": float(amount), "ref_balance": 0, "username": None}
        after = float(amount)
        log(f"Создан новый пользователь {user_id_str} с балансом {after}")
    else:
        balances[user_id_str]["balance"] = balances[user_id_str].get("balance", 0) + float(amount)
        after = balances[user_id_str]["balance"]
        log(f"Баланс пользователя {user_id_str} увеличен: было {before}, добавлено {amount}, стало {after}")
    save_balances(balances)
    msg = f"Ваш баланс пополнен на {float(amount)}₽. Текущий баланс: {after}₽"
    if source:
        msg += f"\nИсточник: {source}"
    notify_user(user_id, msg)
    if admin_id:
        msg_admin = f"Вы пополнили баланс пользователя {user_id} на {float(amount)}₽. Новый баланс: {after}₽"
        notify_user(admin_id, msg_admin)

def deduct_user_balance(user_id, amount, reason="", admin_id=None):
    log(f"Вызван deduct_user_balance(user_id={user_id}, amount={amount}, reason={reason}, admin_id={admin_id})")
    balances = load_balances()
    user_id_str = str(user_id)
    if user_id_str not in balances or not isinstance(balances[user_id_str], dict):
        balances[user_id_str] = {"balance": 0, "ref_balance": 0, "username": None}
        save_balances(balances)
        log(f"Пользователь {user_id_str} не найден при попытке списания, создан с нулевым балансом")
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
        log(f"С пользователя {user_id_str} успешно списано {amount}, остаток: {balances[user_id_str]['balance']}")
        return True
    log(f"Недостаточно средств у пользователя {user_id_str}: текущий баланс {current}, требуется {amount}")
    return False

def minus_user_balance(user_id, amount, reason="", admin_id=None):
    log(f"Вызван minus_user_balance(user_id={user_id}, amount={amount}, reason={reason}, admin_id={admin_id})")
    balances = load_balances()
    user_id_str = str(user_id)
    before = balances.get(user_id_str, {}).get("balance", 0)
    if user_id_str not in balances or not isinstance(balances[user_id_str], dict):
        balances[user_id_str] = {"balance": -float(amount), "ref_balance": 0, "username": None}
        after = -float(amount)
        log(f"Создан новый пользователь {user_id_str} с отрицательным балансом {after}")
    else:
        balances[user_id_str]["balance"] = balances[user_id_str].get("balance", 0) - float(amount)
        after = balances[user_id_str]["balance"]
        log(f"Баланс пользователя {user_id_str} уменьшен: было {before}, списано {amount}, стало {after}")
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
    log(f"Вызван get_ref_balance(user_id={user_id})")
    balances = load_balances()
    user_id_str = str(user_id)
    ref_balance = balances.get(user_id_str, {}).get("ref_balance", 0)
    log(f"Реферальный баланс пользователя {user_id_str}: {ref_balance}")
    return ref_balance

def set_ref_balance(user_id, value, admin_action=False, admin_id=None):
    log(f"Вызван set_ref_balance(user_id={user_id}, value={value}, admin_action={admin_action}, admin_id={admin_id})")
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
        log(f"Реферальный баланс пользователя {user_id_str} изменён: было {before}, стало {value}")

def add_ref_balance(user_id, amount, source="", admin_id=None):
    log(f"Вызван add_ref_balance(user_id={user_id}, amount={amount}, source={source}, admin_id={admin_id})")
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
        log(f"Реферальный баланс пользователя {user_id_str} увеличен: было {before}, добавлено {amount}, стало {after}")

def process_referral_bonus(user_id, amount):
    log(f"Вызван process_referral_bonus(user_id={user_id}, amount={amount})")
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
            log(f"Рефералу {referrer_id} начислен бонус {bonus}₽. Было {before}, стало {after}")
            return bonus, referrer_id
        else:
            log(f"Реферер {referrer_id} не найден в balances")
    else:
        log(f"Пользователь {user_id_str} не имеет реферера")
    return 0, None
