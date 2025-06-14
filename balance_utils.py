import os
import json

# Жёстко задаём путь к файлу в нужной папке
BALANCE_FILE = "/app/data/files212/user_balances.json"

def load_balances():
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_referrer_id(user_id):
    balances = load_balances()
    user_id_str = str(user_id)
    user = balances.get(user_id_str)
    return user.get("referrer_id") if user else None

def save_balances(balances):
    # Гарантируем, что папка существует
    os.makedirs(os.path.dirname(BALANCE_FILE), exist_ok=True)
    with open(BALANCE_FILE, "w", encoding="utf-8") as f:
        json.dump(balances, f, ensure_ascii=False, indent=2)

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
    else:
        save_balances(balances)

def find_user_id_by_username(username):
    """
    Поиск user_id по username (без @, регистр не важен).
    Возвращает int user_id или None.
    """
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
        balances[user_id_str] = {"balance": 0, "username": None}
        save_balances(balances)
    return balances[user_id_str].get("balance", 0)

def set_user_balance(user_id, amount):
    balances = load_balances()
    user_id_str = str(user_id)
    if user_id_str not in balances or not isinstance(balances[user_id_str], dict):
        balances[user_id_str] = {"balance": float(amount), "username": None}
    else:
        balances[user_id_str]["balance"] = float(amount)
    save_balances(balances)

def add_user_balance(user_id, amount):
    balances = load_balances()
    user_id_str = str(user_id)
    if user_id_str not in balances or not isinstance(balances[user_id_str], dict):
        balances[user_id_str] = {"balance": float(amount), "username": None}
    else:
        balances[user_id_str]["balance"] = balances[user_id_str].get("balance", 0) + float(amount)
    save_balances(balances)

def deduct_user_balance(user_id, amount):
    balances = load_balances()
    user_id_str = str(user_id)
    if user_id_str not in balances or not isinstance(balances[user_id_str], dict):
        balances[user_id_str] = {"balance": 0, "username": None}
        save_balances(balances)
        return False
    current = balances[user_id_str].get("balance", 0)
    if current >= float(amount):
        balances[user_id_str]["balance"] = current - float(amount)
        save_balances(balances)
        return True
    return False

def minus_user_balance(user_id, amount):
    balances = load_balances()
    user_id_str = str(user_id)
    if user_id_str not in balances or not isinstance(balances[user_id_str], dict):
        balances[user_id_str] = {"balance": -float(amount), "username": None}
    else:
        balances[user_id_str]["balance"] = balances[user_id_str].get("balance", 0) - float(amount)
    save_balances(balances)


def get_ref_balance(user_id):
    balances = load_balances()
    user_id_str = str(user_id)
    return balances.get(user_id_str, {}).get("ref_balance", 0)

def add_ref_balance(user_id, amount):
    balances = load_balances()
    user_id_str = str(user_id)
    if user_id_str in balances:
        balances[user_id_str]["ref_balance"] = balances[user_id_str].get("ref_balance", 0) + float(amount)
        save_balances(balances)


def process_referral_bonus(user_id, amount):
    balances = load_balances()
    user_id_str = str(user_id)
    user = balances.get(user_id_str)
    if user and user.get("referrer_id"):
        referrer_id = str(user["referrer_id"])
        bonus = round(float(amount) * 0.2, 2)
        if referrer_id in balances:
            balances[referrer_id]["ref_balance"] = balances[referrer_id].get("ref_balance", 0) + bonus
            save_balances(balances)
            return bonus, referrer_id
    return 0, None

def set_ref_balance(user_id, value):
    balances = load_balances()
    user_id_str = str(user_id)
    if user_id_str in balances:
        balances[user_id_str]["ref_balance"] = float(value)
        save_balances(balances)
