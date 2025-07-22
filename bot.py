# -*- coding: utf-8 -*-
import os
import sys
import logging
import asyncio
import re
import shutil
import subprocess
from datetime import datetime
from docx.shared import Pt, Cm
from docx.enum.text import WD_BREAK
from libreoffice_converter import convert
import pdfplumber
from telegram import ReplyKeyboardMarkup
from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from balance_utils import add_user_balance, set_ref_balance
from welcome_menu import show_welcome_menu, welcome_menu_callback
from hint_utils import save_user_hint, get_last_hint, make_hint_keyboard
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackQueryHandler
)
from telegram.error import TelegramError, TimedOut, NetworkError

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BALANCES_PATH = "/app/data/files212/balance_utils/user_balances.json"
# /app/data/files212/user_balances.json

from balance_utils import get_user_balance, deduct_user_balance
from yookassa_api import create_payment

from admin_commands import (
    set_balance_command,
    plus_balance_command,
    minus_balance_command,
    user_balance_command,
)

import random

# === ЛОГ В КОНСОЛЬ И ФАЙЛ ===
today = datetime.now().strftime("%Y-%m-%d")
log_dir = "/app/data/files212/bot/log"
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, f"{today}.txt")

class Tee(object):
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    def flush(self):
        for f in self.files:
            f.flush()

log_file = open(log_path, "a", encoding="utf-8")
sys.stdout = Tee(sys.stdout, log_file)
sys.stderr = Tee(sys.stderr, log_file)

REF_EMOJI = [
    "👶", "🧒", "👦", "👧", "🧑", "👨", "👩", "🧓", "👴", "👵",  # дети, взрослые, пожилые
    "👱", "👱‍♂️", "👱‍♀️", "🧔", "🧔‍♂️", "🧔‍♀️",
    "👲", "👳", "👳‍♂️", "👳‍♀️", "🧕", "👮", "👮‍♂️", "👮‍♀️",
    "👷", "👷‍♂️", "👷‍♀️", "💂", "💂‍♂️", "💂‍♀️", "🕵️", "🕵️‍♂️", "🕵️‍♀️",
    "👩‍⚕️", "👨‍⚕️", "👩‍🎓", "👨‍🎓", "👩‍🏫", "👨‍🏫", "👩‍⚖️", "👨‍⚖️",
    "👩‍🌾", "👨‍🌾", "👩‍🍳", "👨‍🍳", "👩‍🔧", "👨‍🔧", "👩‍🏭", "👨‍🏭",
    "👩‍💼", "👨‍💼", "👩‍🔬", "👨‍🔬", "👩‍💻", "👨‍💻", "👩‍🎤", "👨‍🎤",
    "👩‍🎨", "👨‍🎨", "👩‍✈️", "👨‍✈️", "👩‍🚀", "👨‍🚀", "👩‍🚒", "👨‍🚒",
    "👰", "🤵", "👰‍♂️", "🤵‍♀️", "👸", "🤴", "🥷", "🦸", "🦹",
    "🧙", "🧙‍♂️", "🧙‍♀️", "🧚", "🧚‍♂️", "🧚‍♀️", "🧛", "🧛‍♂️", "🧛‍♀️",
    "🧜", "🧜‍♂️", "🧜‍♀️", "🧝", "🧝‍♂️", "🧝‍♀️", "🧞", "🧞‍♂️", "🧞‍♀️",
    "🧟", "🧟‍♂️", "🧟‍♀️",
    # Семьи, пары традиционные
    "👪", "👨‍👩‍👧", "👨‍👩‍👦", "👨‍👩‍👧‍👦",
    # Жесты и эмоции
    "🙍", "🙍‍♂️", "🙍‍♀️", "🙎", "🙎‍♂️", "🙎‍♀️", "🙅", "🙅‍♂️", "🙅‍♀️",
    "🙆", "🙆‍♂️", "🙆‍♀️", "💁", "💁‍♂️", "💁‍♀️", "🙋", "🙋‍♂️", "🙋‍♀️",
    "🙇", "🙇‍♂️", "🙇‍♀️", "🤦", "🤦‍♂️", "🤦‍♀️", "🤷", "🤷‍♂️", "🤷‍♀️",
    "🧏", "🧏‍♂️", "🧏‍♀️",
    # Спорт и активность
    "🏃", "🏃‍♂️", "🏃‍♀️", "🚶", "🚶‍♂️", "🚶‍♀️", "💃", "🕺", "🧗", "🧗‍♂️", "🧗‍♀️"
]


TOPUP_AMOUNT, TOPUP_EMAIL = range(100, 102)
NEW_TOPIC, NEW_SUBJECT, NEW_FIO, NEW_GROUP, NEW_TEACHER, NEW_POINTS, NEW_SPEC_NUMBER, NEW_SPEC_NAME = range(8)

BOT_RETURN_URL = "https://t.me/yours_projects_bot"
ADMIN_ID = 5236886477

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = os.getenv("DEEPSEEK_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
PROJECTS_PATH = os.path.join(BASE_PATH, 'projects')

# ======================= КНОПКИ =======================
MAIN_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("🖨️ Новый проект", callback_data="new_project")],
    [InlineKeyboardButton("🏦 Баланс", callback_data="balance")],
    [InlineKeyboardButton("💸 Реферальная система", callback_data="referral_menu")],
])

BACK_TO_MENU_BTN = InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu")



async def referral_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_send_and_store(
        context, update.effective_chat.id,
        "Меню реферальной системы. Выберите действие:",
        reply_markup=REFERRAL_MENU
    )

def update_user_info_from_update(update):
    """
    Обновляет username в базе при любом взаимодействии пользователя.
    """
    user = getattr(update, "effective_user", None)
    if user is not None:
        from balance_utils import update_user_info  # импортируй здесь, чтобы не было циклических импортов
        username = getattr(user, "username", None)
        update_user_info(user.id, username)

async def referral_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Меню реферальной системы", reply_markup=REFERRAL_MENU_INLINE)




# =========== ДОБАВЛЕНЫ ФУНКЦИИ ДЛЯ УДАЛЕНИЯ ОСТАТКА КЛАВИАТУРЫ И SAFE SEND ==========
def get_invited_list(user_id):
    """Возвращает список кортежей (uid, username) приглашённых этим user_id."""
    from balance_utils import load_balances  # чтобы не было циклического импорта
    balances = load_balances()
    user_id = str(user_id)
    invited = []
    for uid, data in balances.items():
        # Сравнение только по строке!
        if str(data.get("referrer_id")) == user_id:
            uname = data.get("username") or uid
            invited.append((uid, uname))
    return invited

async def clear_last_bot_keyboard(context, chat_id):
    """Удаляет reply_markup у последнего сообщения бота, если оно было сохранено."""
    msg_id = context.user_data.get("last_msg_id")
    if msg_id:
        try:
            await context.bot.edit_message_reply_markup(chat_id=chat_id, message_id=msg_id, reply_markup=None)
        except Exception as e:
            logger.debug(f"Не удалось удалить клавиатуру: {e}")

async def safe_send_and_store(context, chat_id, *args, **kwargs):
    """Безопасно отправляет сообщение, очищает старую клавиатуру, сохраняет message_id."""
    await clear_last_bot_keyboard(context, chat_id)
    msg = await safe_send_message(context.bot, chat_id, *args, **kwargs)
    if msg:
        context.user_data["last_msg_id"] = msg.message_id
    return msg

async def safe_edit_and_store(context, chat_id, message_id, *args, **kwargs):
    """Безопасно редактирует сообщение, очищает старую клавиатуру, сохраняет message_id."""
    await clear_last_bot_keyboard(context, chat_id)
    try:
        msg = await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, *args, **kwargs)
        context.user_data["last_msg_id"] = msg.message_id
        return msg
    except Exception as e:
        logger.warning(f"Не удалось отредактировать сообщение: {e}")

# =========== ОБНОВЛЁННЫЕ ОСНОВНЫЕ ФУНКЦИИ ПОПОЛНЕНИЯ ==========

async def topup_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_user_info_from_update(update)
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    await clear_last_bot_keyboard(context, chat_id)
    reply_markup = make_hint_keyboard("amount", user_id, BACK_TO_MENU_BTN)
    if update.callback_query:
        await update.callback_query.answer()
        await safe_edit_and_store(
            context, chat_id, update.callback_query.message.message_id,
            "Введи сумму пополнения в рублях. Например: 100",
            reply_markup=reply_markup
        )
    else:
        await safe_send_and_store(
            context, chat_id,
            "Введи сумму пополнения в рублях. Например: 100",
            reply_markup=reply_markup
        )
    return TOPUP_AMOUNT

async def handle_topup_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    await clear_last_bot_keyboard(context, chat_id)

    # Обработка ручного ввода суммы
    if update.message:
        text = update.message.text
        try:
            amount = float(text.replace(",", "."))
            if amount < 10:
                raise ValueError
        except Exception:
            await safe_send_and_store(
                context, chat_id,
                "Пожалуйста, введите сумму (минимум 10 руб):",
                reply_markup=make_hint_keyboard("amount", user_id, BACK_TO_MENU_BTN)
            )
            return TOPUP_AMOUNT

        context.user_data["amount"] = amount
        save_user_hint(user_id, "amount", str(amount))
        await safe_send_and_store(
            context, chat_id,
            "Введи свой email для отправки чека",
            reply_markup=make_hint_keyboard("email", user_id, BACK_TO_MENU_BTN)
        )
        return TOPUP_EMAIL

    # Обработка нажатия на подсказку для суммы
    elif update.callback_query and update.callback_query.data == "hint_amount":
        amount_text = get_last_hint(user_id, "amount")
        try:
            amount = float(amount_text.replace(",", "."))
            if amount < 10:
                raise ValueError
        except Exception:
            await update.callback_query.answer()
            await safe_edit_and_store(
                context, chat_id, update.callback_query.message.message_id,
                "Пожалуйста, введите сумму (минимум 10 руб):",
                reply_markup=make_hint_keyboard("amount", user_id, BACK_TO_MENU_BTN)
            )
            return TOPUP_AMOUNT

        context.user_data["amount"] = amount
        save_user_hint(user_id, "amount", str(amount))
        await update.callback_query.answer()
        await safe_edit_and_store(
            context, chat_id, update.callback_query.message.message_id,
            "Введи свой email для отправки чека",
            reply_markup=make_hint_keyboard("email", user_id, BACK_TO_MENU_BTN)
        )
        return TOPUP_EMAIL

async def handle_topup_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    await clear_last_bot_keyboard(context, chat_id)
    amount = context.user_data.get("amount")

    # Проверка наличия суммы
    if amount is None:
        if update.callback_query:
            await update.callback_query.answer()
            await safe_edit_and_store(
                context, chat_id, update.callback_query.message.message_id,
                "Ошибка: сумма не найдена. Начните заново с меню.",
                reply_markup=MAIN_MENU
            )
        else:
            await safe_send_and_store(
                context, chat_id,
                "Ошибка: сумма не найдена. Начните заново с /topup.",
                reply_markup=BACK_TO_MENU_BTN
            )
        context.user_data.pop("amount", None)
        return ConversationHandler.END

    # Ручной ввод email
    if update.message:
        email = update.message.text.strip()
        if not is_valid_email(email):
            await safe_send_and_store(
                context, chat_id,
                "Пожалуйста, введите корректный email (например, name@example.com):",
                reply_markup=make_hint_keyboard("email", user_id, BACK_TO_MENU_BTN)
            )
            return TOPUP_EMAIL

        context.user_data["email"] = email
        save_user_hint(user_id, "email", email)
        # Далее создание платежа и переход к оплате
        try:
            description = f"Пополнение баланса для Telegram user_id {user_id}"
            payment = create_payment(amount, description, BOT_RETURN_URL, user_id, email)
            pay_url = payment["confirmation"]["confirmation_url"]

            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Оплатить", url=pay_url)],
                [InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu")]
            ])
            await safe_send_and_store(
                context, chat_id,
                "Оплати по кнопке ниже.\n\nПосле оплаты баланс пополнится автоматически",
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Ошибка при создании платежа: {e}")
            await safe_send_and_store(
                context, chat_id,
                f"Ошибка при создании платежа: {e}",
                reply_markup=BACK_TO_MENU_BTN
            )
        context.user_data.pop("amount", None)
        return ConversationHandler.END

    # Нажатие на подсказку (hint_email)
    elif update.callback_query and update.callback_query.data == "hint_email":
        email = get_last_hint(user_id, "email")
        if not is_valid_email(email):
            await update.callback_query.answer()
            await safe_edit_and_store(
                context, chat_id, update.callback_query.message.message_id,
                "Пожалуйста, введите корректный email (например, name@example.com):",
                reply_markup=make_hint_keyboard("email", user_id, BACK_TO_MENU_BTN)
            )
            return TOPUP_EMAIL

        context.user_data["email"] = email
        save_user_hint(user_id, "email", email)
        try:
            description = f"Пополнение баланса для Telegram user_id {user_id}"
            payment = create_payment(amount, description, BOT_RETURN_URL, user_id, email)
            pay_url = payment["confirmation"]["confirmation_url"]

            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Оплатить", url=pay_url)],
                [InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu")]
            ])
            await update.callback_query.answer()
            await safe_edit_and_store(
                context, chat_id, update.callback_query.message.message_id,
                "Оплати по кнопке ниже.\n\nПосле оплаты баланс пополнится автоматически",
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Ошибка при создании платежа: {e}")
            await update.callback_query.answer()
            await safe_edit_and_store(
                context, chat_id, update.callback_query.message.message_id,
                f"Ошибка при создании платежа: {e}",
                reply_markup=BACK_TO_MENU_BTN
            )
        context.user_data.pop("amount", None)
        return ConversationHandler.END

# ===============================================


# Ваш обработчик
async def referral_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # Показываем меню рефералки (пример!)
    await query.edit_message_text(
        "Меню реферальной системы. Выберите действие:",
        reply_markup=REFERRAL_MENU_INLINE  # Твоя клавиатура для рефералки, смотри ниже
    )

REFERRAL_MENU_INLINE = InlineKeyboardMarkup([
    [InlineKeyboardButton("👥 Приглашённые", callback_data="ref_invited")],
    [InlineKeyboardButton("🔗 Моя реферальная ссылка", callback_data="ref_link")],
    [InlineKeyboardButton("🏦 Мой реферальный баланс", callback_data="ref_balance")],
    [InlineKeyboardButton("💳 Вывести на карту", callback_data="ref_withdraw")],
    [InlineKeyboardButton("🔄 Перевести на баланс", callback_data="ref_to_main")],
    [InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu")],
])

def load_balances():
    """Загружает словарь балансов пользователей из user_balances.json."""
    if not os.path.exists(BALANCES_PATH):
        return {}
    try:
        with open(BALANCES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка при чтении {BALANCES_PATH}: {e}")
        return {}

async def referral_invited_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    invited = get_invited_list(user_id)  # [(uid, uname), ...]
    if invited:
        buttons = []
        for uid, uname in invited:
            emoji = random.choice(REF_EMOJI)
            tg_link = f"https://t.me/{uname}" if uname else ""
            btn_text = f"{emoji} {uname}"
            buttons.append([InlineKeyboardButton(btn_text, url=tg_link)])
        buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="referral_menu")])
        markup = InlineKeyboardMarkup(buttons)
        text = f"У вас {len(invited)} приглашённых:\nНажми на имя для перехода их в Telegram."
        await query.edit_message_text(text, reply_markup=markup)
    else:
        await query.edit_message_text("У тебя пока нет приглашённых. Отправь свою реферальную ссылку знакомым, чтобы получать по 20% от их пополнений", reply_markup=REFERRAL_MENU_INLINE)

async def referral_link_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    bot_username = context.bot.username
    link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    # Кнопка-ссылка + кнопка назад
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад", callback_data="referral_menu")]
    ])

    await query.edit_message_text(
        text=f"Твоя реферальная ссылка:\n```\n{link}\n```\n*Нажми, чтобы скопировать*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

def get_ref_balance(user_id):
    """
    Возвращает реферальный баланс пользователя по user_id.
    """
    user_id = str(user_id)
    from balance_utils import load_balances  # если load_balances уже импортирована, эту строку убери
    balances = load_balances()
    return balances.get(user_id, {}).get("ref_balance", 0)

async def referral_balance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    ref_balance = get_ref_balance(user_id)
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад в реферальное меню", callback_data="referral_menu")]
    ])
    await query.edit_message_text(
        f"Твой реферальный баланс: {ref_balance}₽",
        reply_markup=reply_markup
    )

ASK_AMOUNT = 1

async def referral_to_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    ref_balance = get_ref_balance(user_id)

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад в реферальное меню", callback_data="referral_menu")]
    ])

    if ref_balance < 1:
        await query.edit_message_text(
            "На твоем реферальном балансе недостаточно средств для перевода.",
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    await query.edit_message_text(
        f"Твой реферальный баланс: {ref_balance}₽\n\n"
        "Введи сумму для перевода на основной баланс:",
        reply_markup=reply_markup
    )
    context.user_data['ref_balance'] = ref_balance
    return ASK_AMOUNT

async def referral_to_main_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ref_balance = context.user_data.get('ref_balance', 0)
    text = update.message.text

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад в реферальное меню", callback_data="referral_menu")]
    ])

    try:
        amount = int(text)
    except ValueError:
        await update.message.reply_text(
            "Пожалуйста, введите корректную сумму (целое число).",
            reply_markup=reply_markup
        )
        return ASK_AMOUNT

    if amount < 1 or amount > ref_balance:
        await update.message.reply_text(
            f"Сумма должна быть от 1 до {ref_balance}₽.",
            reply_markup=reply_markup
        )
        return ASK_AMOUNT

    add_user_balance(user_id, amount)
    set_ref_balance(user_id, ref_balance - amount)

    await update.message.reply_text(
        f"{amount}₽ успешно переведено на твой основной баланс.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

REF_WITHDRAW_SUM, REF_WITHDRAW_PHONE, REF_WITHDRAW_BANK = range(3)

def referral_menu_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад в реферальное меню", callback_data="referral_menu")]
    ])

async def referral_withdraw_callback(update, context):
    ref_balance = get_ref_balance(update.effective_user.id)
    if ref_balance < 1:
        await update.callback_query.edit_message_text(
            "На твое реферальном балансе недостаточно средств.",
            reply_markup=referral_menu_markup()
        )
        return ConversationHandler.END
    await update.callback_query.edit_message_text(
        f"На твоем реферальном балансе {ref_balance}₽.\n\nВведи сумму для вывода:",
        reply_markup=referral_menu_markup()
    )
    return REF_WITHDRAW_SUM

async def referral_withdraw_sum(update, context):
    try:
        amount = float(update.message.text.replace(",", "."))
    except:
        await update.message.reply_text(
            "Введите корректную сумму.",
            reply_markup=referral_menu_markup()
        )
        return REF_WITHDRAW_SUM
    ref_balance = get_ref_balance(update.effective_user.id)
    if amount < 1 or amount > ref_balance:
        await update.message.reply_text(
            f"Введите сумму от 1 до {ref_balance}₽.",
            reply_markup=referral_menu_markup()
        )
        return REF_WITHDRAW_SUM
    context.user_data['withdraw_amount'] = amount
    await update.message.reply_text(
        "Укажите номер телефона для перевода (СБП):",
        reply_markup=referral_menu_markup()
    )
    return REF_WITHDRAW_PHONE

async def referral_withdraw_phone(update, context):
    context.user_data['withdraw_phone'] = update.message.text.strip()
    await update.message.reply_text(
        "Укажите банк для перевода (СБП):",
        reply_markup=referral_menu_markup()
    )
    return REF_WITHDRAW_BANK

async def referral_withdraw_bank(update, context):
    context.user_data['withdraw_bank'] = update.message.text.strip()
    amount = context.user_data['withdraw_amount']
    phone = context.user_data['withdraw_phone']
    bank = context.user_data['withdraw_bank']
    user = update.effective_user

    # Отправляем заявку админам
    admin_id = ADMIN_ID  # или рассылка всем
    await context.bot.send_message(
        admin_id,
        f"Заявка на вывод с рефералки.\n\n"
        f"Username: @{user.username}\n"
        f"Сумма вывода: {amount}\n"
        f"Банк для СБП: {bank}\n"
        f"Номер телефона: {phone}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Отправлено", callback_data=f"ref_withdraw_ok_{user.id}_{amount}"),
             InlineKeyboardButton("❌ Отклонить", callback_data=f"ref_withdraw_decline_{user.id}_{amount}")]
        ])
    )
    await update.message.reply_text(
        "Заявка отправлена модераторам.",
        reply_markup=referral_menu_markup()
    )
    return ConversationHandler.END

async def referral_admin_callback(update, context):
    query = update.callback_query
    data = query.data
    parts = data.split("_")
    action = parts[2]  # 'ok' или 'decline'
    user_id = int(parts[3])
    amount = float(parts[4])
    if action == "ok":
        set_ref_balance(user_id, get_ref_balance(user_id) - amount)
        await context.bot.send_message(
            user_id,
            f"✅ Твоя заявка на вывод {amount}₽ с реферального баланса успешно обработана!",
            reply_markup=referral_menu_markup()
        )
        await query.edit_message_text("✅ Заявка отмечена как выполненная.")
    elif action == "decline":
        await context.bot.send_message(
            user_id,
            "❌ Твоя заявка на вывод с реферального баланса отклонена модератором.",
            reply_markup=referral_menu_markup()
        )
        await query.edit_message_text("❌ Заявка отклонена.")



async def menu_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.chat_data.clear()
    return await start(update, context)

topup_conv = ConversationHandler(
    entry_points=[
        CommandHandler("topup", topup_balance),
        CallbackQueryHandler(topup_balance, pattern="^topup$"),
    ],
    states={
        TOPUP_AMOUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_topup_amount),
            CallbackQueryHandler(handle_topup_amount, pattern="^hint_amount$"),
        ],
        TOPUP_EMAIL: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_topup_email),
            CallbackQueryHandler(handle_topup_email, pattern="^hint_email$"),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(menu_fallback, pattern="^menu$")
    ],
    allow_reentry=True,
)

# ======================= Вспомогательные функции =======================

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def is_bold(fontname):
    return any(word in fontname.lower() for word in ["bold", "bd", "black", "heavy", "semibold"])

def create_project_directory():
    if not os.path.exists(PROJECTS_PATH):
        os.makedirs(PROJECTS_PATH)
        logger.info("Создана папка projects")

async def safe_send_message(bot, chat_id, *args, **kwargs):
    for i in range(20):
        try:
            return await bot.send_message(chat_id, *args, **kwargs)
        except (TimedOut, NetworkError, TelegramError) as e:
            logger.warning(f"safe_send_message попытка {i+1}: {e}")
            await asyncio.sleep(2 * (i + 1))
    logger.error(f"Не удалось отправить сообщение после 20 попыток: {args}, {kwargs}")

# ======================= КНОПОЧНЫЕ ОБРАБОТЧИКИ =======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args if hasattr(context, 'args') else []
    referrer_id = None
    
    # Обработка реферальной ссылки
    if args and args[0].startswith('ref_'):
        try:
            referrer_id = int(args[0][4:])
        except Exception:
            referrer_id = None

    # Регистрация пользователя и обновление username/referrer_id
    from balance_utils import update_user_info, load_balances
    balances = load_balances()
    user_id_str = str(user.id)
    if user_id_str not in balances:
        update_user_info(user.id, user.username, referrer_id)
        from welcome_menu import show_welcome_menu
        await show_welcome_menu(update, context)
        return ConversationHandler.END
    else:
        update_user_info(user.id, user.username)

    # Формируем реферальную ссылку
    bot_username = context.bot.username if hasattr(context.bot, 'username') else "bot"
    my_ref_link = f"https://t.me/{bot_username}?start=ref_{user.id}"

    # Список приглашённых
    invited = []
    for uid, data in balances.items():
        if data.get("referrer_id") == user.id:
            invited.append(data.get("username") or uid)
    ref_balance = balances.get(user_id_str, {}).get("ref_balance", 0)

    invited_text = "\n".join([f"- {name}" for name in invited]) or "Пока нет приглашённых."

    text = (
        "*«Твои проекты»* - быстро, просто, бюджетно.\n\n"
        "Выбери действие:"
    )

    # Удаляем инлайн-клавиатуру с прошлого сообщения, если она была
    await clear_last_bot_keyboard(context, update.effective_chat.id)
    # Очищаем состояния
    context.user_data.clear()

    # Принудительный сброс состояния conversation
    for key in list(context.chat_data.keys()):
        if "conversation" in key:
            del context.chat_data[key]

    
    context.chat_data.clear()
    
    # Приветствие и меню
    if update.message:
        await safe_send_and_store(context, update.effective_chat.id, text, reply_markup=MAIN_MENU, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.answer()
        await safe_edit_and_store(
            context,
            update.effective_chat.id,
            update.callback_query.message.message_id,
            text,
            reply_markup=MAIN_MENU,
            parse_mode="Markdown"   # <--- вот это!
        )
    return ConversationHandler.END

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start(update, context)

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "menu":
        return await menu_callback(update, context)
    elif action == "new_project":
        return await new_progect_start(update, context, from_menu=True)
    elif action == "balance":
        return await show_balance(update, context, from_menu=True)
    elif action == "topup":
        return await topup_balance_menu(update, context)
    return ConversationHandler.END

async def new_progect_start(update: Update, context: ContextTypes.DEFAULT_TYPE, from_menu=False) -> int:
    context.user_data.clear()
    context.chat_data.clear()
    await clear_last_bot_keyboard(context, update.effective_chat.id)
    user_id = update.effective_user.id
    reply_markup = make_hint_keyboard("topic", user_id, BACK_TO_MENU_BTN)

    if from_menu and update.callback_query:
        await safe_edit_and_store(
            context,
            update.effective_chat.id,
            update.callback_query.message.message_id,
            "Отправь мне тему, по которой пишешь проект",
            reply_markup=reply_markup
        )
    else:
        await safe_send_and_store(
            context,
            update.effective_chat.id,
            "Отправь мне тему, по которой пишешь проект",
            reply_markup=reply_markup
        )
    return NEW_TOPIC

BALANCE_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("💳 Пополнить баланс", callback_data="topup")],
    [InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu")]
])

async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE, from_menu=False):
    update_user_info_from_update(update)
    balance = int(get_user_balance(update.effective_user.id))
    text = f"*Твой баланс*: {balance}₽"
    await clear_last_bot_keyboard(context, update.effective_chat.id)
    if from_menu and update.callback_query:
        await safe_edit_and_store(
            context, 
            update.effective_chat.id, 
            update.callback_query.message.message_id, 
            text, 
            reply_markup=BALANCE_MENU, 
            parse_mode="Markdown"
        )
    else:
        await safe_send_and_store(
            context, 
            update.effective_chat.id, 
            text, 
            reply_markup=BALANCE_MENU, 
            parse_mode="Markdown"
        )

async def topup_balance_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await clear_last_bot_keyboard(context, update.effective_chat.id)
    if update.callback_query:
        await safe_edit_and_store(context, update.effective_chat.id, update.callback_query.message.message_id,
            "Введи сумму пополнения в рублях. Например: 100", reply_markup=BACK_TO_MENU_BTN)
    else:
        await safe_send_and_store(context, update.effective_chat.id, "Введи сумму пополнения в рублях. Например: 100", reply_markup=BACK_TO_MENU_BTN)
    return TOPUP_AMOUNT

# ========== ДАЛЬШЕ ВСЁ СТАНДАРТНО, КРОМЕ ДОБАВЛЕНИЯ reply_markup=BACK_TO_MENU_BTN в safe_send_message там где вручную ==========
async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def example(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def new_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if update.message:
        topic = update.message.text
        context.user_data['topic'] = topic
        save_user_hint(user_id, "topic", topic)
        await safe_send_and_store(
            context, update.effective_chat.id, 
            "Отправь предмет, по которому готовишь проект", 
            reply_markup=make_hint_keyboard("subject", user_id, BACK_TO_MENU_BTN)
        )
        return NEW_SUBJECT
    elif update.callback_query and update.callback_query.data == "hint_topic":
        topic = get_last_hint(user_id, "topic")
        context.user_data['topic'] = topic
        save_user_hint(user_id, "topic", topic)
        await update.callback_query.answer()
        await safe_edit_and_store(
            context, update.effective_chat.id, update.callback_query.message.message_id,
            "Отправь предмет, по которому готовишь проект",
            reply_markup=make_hint_keyboard("subject", user_id, BACK_TO_MENU_BTN)
        )
        return NEW_SUBJECT

async def new_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if update.message:
        subject = update.message.text
        context.user_data['subject'] = subject
        save_user_hint(user_id, "subject", subject)
        await safe_send_and_store(
            context, update.effective_chat.id,
            "Отправь мне свое ФИО. (Для титулки)",
            reply_markup=make_hint_keyboard("fio_student", user_id, BACK_TO_MENU_BTN)
        )
        return NEW_FIO
    elif update.callback_query and update.callback_query.data == "hint_subject":
        subject = get_last_hint(user_id, "subject")
        context.user_data['subject'] = subject
        save_user_hint(user_id, "subject", subject)
        await update.callback_query.answer()
        await safe_edit_and_store(
            context, update.effective_chat.id, update.callback_query.message.message_id,
            "Отправь мне свое ФИО. (Для титулки)",
            reply_markup=make_hint_keyboard("fio_student", user_id, BACK_TO_MENU_BTN)
        )
        return NEW_FIO

async def new_fio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if update.message:
        fio = update.message.text
        context.user_data['fio_student'] = fio
        save_user_hint(user_id, "fio_student", fio)
        await safe_send_and_store(
            context, update.effective_chat.id,
            "Отправь группу, в которой учишься. (Для титулки)",
            reply_markup=make_hint_keyboard("group", user_id, BACK_TO_MENU_BTN)
        )
        return NEW_GROUP
    elif update.callback_query and update.callback_query.data == "hint_fio_student":
        fio = get_last_hint(user_id, "fio_student")
        context.user_data['fio_student'] = fio
        save_user_hint(user_id, "fio_student", fio)
        await update.callback_query.answer()
        await safe_edit_and_store(
            context, update.effective_chat.id, update.callback_query.message.message_id,
            "Отправь группу, в которой учишься. (Для титулки)",
            reply_markup=make_hint_keyboard("group", user_id, BACK_TO_MENU_BTN)
        )
        return NEW_GROUP

def get_spec_by_group(group):
    group = group.upper()
    if "ТОД" in group:
        return "23.02.07", "Техническое обслуживание и ремонт двигателей, систем и агрегатов автомобилей"
    elif "ЭТ" in group:
        return "23.02.05", "Эксплуатация транспортного электрооборудования и автоматики (по видам транспорта, за исключением водного)"
    elif "СД" in group:
        return "08.02.12", "Строительство и эксплуатация автомобильных дорог, аэродромов и городских путей сообщения"
    elif "ОП" in group:
        return "23.02.01", "Организация перевозок и управление на транспорте (по видам)"
    else:
        return "", ""

async def new_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    if update.message:
        group = update.message.text

    elif update.callback_query and update.callback_query.data == "hint_group":
        group = get_last_hint(user_id, "group")
        context.user_data['group'] = group
        save_user_hint(user_id, "group", group)

        spec_number, spec_name = get_spec_by_group(group)
        if not spec_number or not spec_name:
            await update.callback_query.answer()
            await safe_edit_and_store(
                context, update.effective_chat.id, update.callback_query.message.message_id,
                "Отправь код своей специальности, по ФГОС. Например: 23.02.07",
                reply_markup=make_hint_keyboard("spec_number", user_id, BACK_TO_MENU_BTN)
            )
            return NEW_SPEC_NUMBER

        context.user_data['spec_number'] = spec_number
        context.user_data['spec_name'] = spec_name
        await update.callback_query.answer()
        await safe_edit_and_store(
            context, update.effective_chat.id, update.callback_query.message.message_id,
            "Введи ФИО преподавателя",
            reply_markup=make_hint_keyboard("fio_teacher", user_id, BACK_TO_MENU_BTN)
        )
        return NEW_TEACHER

    else:
        return NEW_GROUP

    # сюда попадаем только при ручном вводе
    context.user_data['group'] = group
    save_user_hint(user_id, "group", group)

    spec_number, spec_name = get_spec_by_group(group)
    if not spec_number or not spec_name:
        await safe_send_and_store(
            context, update.effective_chat.id,
            "Отправь код своей специальности, по ФГОС. Например: 23.02.07",
            reply_markup=make_hint_keyboard("spec_number", user_id, BACK_TO_MENU_BTN)
        )
        return NEW_SPEC_NUMBER

    context.user_data['spec_number'] = spec_number
    context.user_data['spec_name'] = spec_name
    await safe_send_and_store(
        context, update.effective_chat.id,
        "Введи ФИО преподавателя",
        reply_markup=make_hint_keyboard("fio_teacher", user_id, BACK_TO_MENU_BTN)
    )
    return NEW_TEACHER


async def new_spec_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    if update.message:
        spec_number = update.message.text

    elif update.callback_query and update.callback_query.data == "hint_spec_number":
        spec_number = get_last_hint(user_id, "spec_number")
        context.user_data['spec_number'] = spec_number
        save_user_hint(user_id, "spec_number", spec_number)

        await update.callback_query.answer()
        await safe_edit_and_store(
            context, update.effective_chat.id, update.callback_query.message.message_id,
            "Теперь введи полное название специальности, по ФГОС. Например: Техническое обслуживание и ремонт двигателей, систем и агрегатов автомобилей",
            reply_markup=make_hint_keyboard("spec_name", user_id, BACK_TO_MENU_BTN)
        )
        return NEW_SPEC_NAME  # ← важно: возвращаем здесь, чтобы не упасть в send_and_store ниже

    else:
        return NEW_SPEC_NUMBER

    # ручной ввод
    context.user_data['spec_number'] = spec_number
    save_user_hint(user_id, "spec_number", spec_number)

    await safe_send_and_store(
        context, update.effective_chat.id,
        "Теперь введи полное название специальности, по ФГОС. Например: Техническое обслуживание и ремонт двигателей, систем и агрегатов автомобилей",
        reply_markup=make_hint_keyboard("spec_name", user_id, BACK_TO_MENU_BTN)
    )
    return NEW_SPEC_NAME

async def new_spec_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    if update.message:
        spec_name = update.message.text

    elif update.callback_query and update.callback_query.data == "hint_spec_name":
        spec_name = get_last_hint(user_id, "spec_name")
        context.user_data['spec_name'] = spec_name
        save_user_hint(user_id, "spec_name", spec_name)

        await update.callback_query.answer()
        await safe_edit_and_store(
            context, update.effective_chat.id, update.callback_query.message.message_id,
            "Введи ФИО преподавателя",
            reply_markup=make_hint_keyboard("fio_teacher", user_id, BACK_TO_MENU_BTN)
        )
        return NEW_TEACHER  # ← не даём провалиться в send_and_store ниже

    else:
        return NEW_SPEC_NAME

    # ручной ввод
    context.user_data['spec_name'] = spec_name
    save_user_hint(user_id, "spec_name", spec_name)

    await safe_send_and_store(
        context, update.effective_chat.id,
        "Введи ФИО преподавателя",
        reply_markup=make_hint_keyboard("fio_teacher", user_id, BACK_TO_MENU_BTN)
    )
    return NEW_TEACHER


async def new_teacher(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    if update.message:
        fio_teacher = update.message.text
        context.user_data['fio_teacher'] = fio_teacher
        save_user_hint(user_id, "fio_teacher", fio_teacher)
        await safe_send_and_store(
            context, update.effective_chat.id,
            "Введи количество разделов. 1 раздел",
            reply_markup=make_hint_keyboard("num_points", user_id, BACK_TO_MENU_BTN)
        )
        return NEW_POINTS

    elif update.callback_query and update.callback_query.data == "hint_fio_teacher":
        fio_teacher = get_last_hint(user_id, "fio_teacher")
        context.user_data['fio_teacher'] = fio_teacher
        save_user_hint(user_id, "fio_teacher", fio_teacher)
        await update.callback_query.answer()
        await safe_edit_and_store(
            context, update.effective_chat.id, update.callback_query.message.message_id,
            "Введи количество разделов проекта. 1 раздел = 20 ₽ (~1,5 страницы текста)",
            reply_markup=make_hint_keyboard("num_points", user_id, BACK_TO_MENU_BTN)
        )
        return NEW_POINTS

    else:
        return NEW_TEACHER


async def new_points(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    # Если пользователь только пришёл на этап (после new_teacher), показываем клавиатуру с подсказками
    if not (update.message or (update.callback_query and update.callback_query.data == "hint_num_points")):
        await safe_send_and_store(
            context, update.effective_chat.id,
            "Введи количество разделов проекта. 1 раздел = 20 ₽ (~1,5 страницы текста)",
            reply_markup=make_hint_keyboard("num_points", user_id, BACK_TO_MENU_BTN)
        )
        return NEW_POINTS

    if update.message:
        text = update.message.text
        try:
            num_points = int(text)
            if num_points <= 0:
                raise ValueError
            context.user_data['num_points'] = num_points
            save_user_hint(user_id, "num_points", text)
        except ValueError:
            await safe_send_and_store(
                context, update.effective_chat.id,
                "Введи натуральное число. Например: 1, 2, 3 и т.д.",
                reply_markup=make_hint_keyboard("num_points", user_id, BACK_TO_MENU_BTN)
            )
            return NEW_POINTS

    elif update.callback_query and update.callback_query.data == "hint_num_points":
        text = get_last_hint(user_id, "num_points")
        await update.callback_query.answer()
        await safe_edit_and_store(
            context, update.effective_chat.id, update.callback_query.message.message_id,
            "Введи количество разделов проекта. 1 раздел = 20 ₽ (~1,5 страницы текста)",
            reply_markup=make_hint_keyboard("num_points", user_id, BACK_TO_MENU_BTN)
        )
        context.user_data['num_points'] = text
        save_user_hint(user_id, "num_points", text)
        try:
            num_points = int(text)
            if num_points <= 0:
                raise ValueError
        except ValueError:
            await safe_send_and_store(
                context, update.effective_chat.id,
                "Введи натуральное число. Например: 1, 2, 3 и т.д.",
                reply_markup=make_hint_keyboard("num_points", user_id, BACK_TO_MENU_BTN)
            )
            return NEW_POINTS

    # Если дошли сюда — число валидно, продолжаем дальше (баланс, генерация и т.д.)
    price = int(context.user_data['num_points']) * 20
    balance = get_user_balance(user_id)
    if balance < price:
        await safe_send_and_store(
            context, update.effective_chat.id,
            f"На твоем балансе недостаточно средств ({balance}₽ / {price}₽).\nПополни баланс кнопкой ниже и попробуй снова",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Пополнить баланс", callback_data="topup")],
                [InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu")]
            ])
        )
        return ConversationHandler.END
    else:
        deduct_user_balance(user_id, price)
        await safe_send_and_store(
            context, update.effective_chat.id,
            f"Генерация проекта начата",
            reply_markup=BACK_TO_MENU_BTN
        )

        # --- запуск генератора ---
        generator_path = os.path.join(os.path.dirname(__file__), "generate_project_process.py")
        subprocess.Popen([
            sys.executable, generator_path,
            "--token", TELEGRAM_BOT_TOKEN,
            "--user_id", str(user_id),
            "--fio_student", context.user_data.get('fio_student', ''),
            "--topic", context.user_data.get('topic', ''),
            "--subject", context.user_data.get('subject', ''),
            "--group", context.user_data.get('group', ''),
            "--fio_teacher", context.user_data.get('fio_teacher', ''),
            "--num_points", str(context.user_data.get('num_points', 1)),
            "--spec_number", context.user_data.get('spec_number', ''),
            "--spec_name", context.user_data.get('spec_name', ''),
            "--primer_path", os.path.join(PROJECTS_PATH, "primer.docx"),
            "--output_dir", PROJECTS_PATH,
            "--deepseek_api_key", API_KEY,
            "--admin_id", str(ADMIN_ID),
        ])
        return ConversationHandler.END

async def error_handler(update, context):
    logger.error(f"Exception: {context.error}")
    user_info = ""
    if update is not None and getattr(update, "effective_user", None) is not None:
        user = update.effective_user
        user_info = f"Ошибка у пользователя @{getattr(user, 'username', None)} ({getattr(user, 'id', None)}): "
    else:
        user_info = "❗️Глобальная ошибка (нет пользователя): "
    try:
        await safe_send_message(
            context.bot,
            ADMIN_ID,
            f"{user_info}{context.error}"
        )
    except Exception as e:
        logger.error(f"Ошибка при попытке отправить админу: {e}")

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    new_proj_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(main_menu_handler, pattern="^new_project$"),
            CommandHandler("new_progect", new_progect_start),
        ],
        states={
            NEW_TOPIC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, new_topic),
                CallbackQueryHandler(new_topic, pattern="^hint_topic$"),
            ],
            NEW_SUBJECT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, new_subject),
                CallbackQueryHandler(new_subject, pattern="^hint_subject$"),
            ],
            NEW_FIO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, new_fio),
                CallbackQueryHandler(new_fio, pattern="^hint_fio_student$"),
            ],
            NEW_GROUP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, new_group),
                CallbackQueryHandler(new_group, pattern="^hint_group$"),
            ],
            NEW_SPEC_NUMBER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, new_spec_number),
                CallbackQueryHandler(new_spec_number, pattern="^hint_spec_number$"),
            ],
            NEW_SPEC_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, new_spec_name),
                CallbackQueryHandler(new_spec_name, pattern="^hint_spec_name$"),
            ],
            NEW_TEACHER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, new_teacher),
                CallbackQueryHandler(new_teacher, pattern="^hint_fio_teacher$"),
            ],
            NEW_POINTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, new_points),
                CallbackQueryHandler(new_points, pattern="^hint_num_points$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(menu_callback, pattern="^menu$"),
            CommandHandler("start", start),
            CommandHandler("new_progect", new_progect_start),
        ],
    )

    application.add_handler(CallbackQueryHandler(welcome_menu_callback, pattern="^welcome_"))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(topup_conv)
    application.add_handler(new_proj_conv)
    application.add_handler(CallbackQueryHandler(main_menu_handler, pattern="^(menu|new_project|balance|topup)$"))

    application.add_handler(CommandHandler("set_balance", set_balance_command))
    application.add_handler(CommandHandler("plus_balance", plus_balance_command))
    application.add_handler(CommandHandler("minus_balance", minus_balance_command))
    application.add_handler(CommandHandler("user_balance", user_balance_command))
    application.add_handler(CallbackQueryHandler(referral_menu_callback, pattern="^referral_menu$"))
    application.add_handler(CallbackQueryHandler(referral_invited_callback, pattern="^ref_invited$"))
    application.add_handler(CallbackQueryHandler(referral_link_callback, pattern="^ref_link$"))
    application.add_handler(CallbackQueryHandler(referral_balance_callback, pattern="^ref_balance$"))
    

    referral_withdraw_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(referral_withdraw_callback, pattern="^ref_withdraw$")],
        states={
            REF_WITHDRAW_SUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, referral_withdraw_sum)],
            REF_WITHDRAW_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, referral_withdraw_phone)],
            REF_WITHDRAW_BANK: [MessageHandler(filters.TEXT & ~filters.COMMAND, referral_withdraw_bank)],
        },
        fallbacks=[CallbackQueryHandler(referral_withdraw_callback, pattern="^ref_withdraw$")],
        per_user=True,
        per_chat=True,
    )
    application.add_handler(referral_withdraw_conv)
    application.add_handler(CallbackQueryHandler(referral_admin_callback, pattern="^ref_withdraw_(ok|decline)_"))

    referral_to_main_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(referral_to_main_callback, pattern="^ref_to_main$")],
        states={
            ASK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, referral_to_main_amount)],
        },
        fallbacks=[CallbackQueryHandler(referral_to_main_callback, pattern="^ref_to_main$")],
        per_user=True,
        per_chat=True,
    )
    application.add_handler(referral_to_main_conv)

    application.add_error_handler(error_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
