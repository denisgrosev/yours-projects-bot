import os
import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, InputMediaPhoto
from telegram.ext import ContextTypes

# Логгер
LOG_DIR = "/app/data/files212/welcome_menu/log"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "log.txt")

def log_event(event, **kwargs):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    parts = [f"[{now}] {event}"]
    for k, v in kwargs.items():
        parts.append(f"{k}={v!r}")
    line = " | ".join(parts)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass

WELCOME_TEXT = (
    "Привет! Это бот «Твои проекты🖨️», который автоматически создаёт учебные работы (проекты, доклады, рефераты) по твоей теме и предмету. Забудь о бессонных ночах — бот всё сделает быстро и качественно."
)

COST_TEXT = (
    "💰 Стоимость\n"
    "– 1 раздел = 20 ₽ (~1,5 страницы текста).\n"
    "– Минимальный заказ — 1 раздел.\n"
    "– Честная оплата: мы сотрудничаем с ЮKassa, это гарантирует безопасность и простоту платежей"
)

PAY_TEXT = (
    "💳 Оплата\n"
    "– Через СБП: мгновенно и без комиссии.\n"
    "– Баланс пополняется автоматически — почти моментально.\n"
    "– Помимо СБП имеются и другие способы оплаты (SberPay, Mir Pay, ЮMoney)"
)

REF_TEXT = (
    "👥 Реферальная система\n"
    "– Приглашай друзей и получай 20 % от каждого их пополнения.\n"
    "– Бонусы мгновенно зачисляются на твой баланс.\n"
    "– Реферальные деньги можно вывести на банковскую карту или перевести в баланс для заказов.\n"
    "– Свою ссылку и статистику приглашений смотри в разделе «Реферальная система»."
)

WELCOME_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("💰 Стоимость?", callback_data="welcome_cost")],
])

COST_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("💳 Как оплатить?", callback_data="welcome_pay")],
    [InlineKeyboardButton("⬅️ Назад", callback_data="welcome_back_to_hello")],
])

PAY_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("👥 Как заработать?", callback_data="welcome_ref")],
    [InlineKeyboardButton("⬅️ Назад", callback_data="welcome_cost")],
])

REF_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("🟢 Начать", callback_data="welcome_start")],
    [InlineKeyboardButton("⬅️ Назад", callback_data="welcome_pay")],
])

EXAMPLE_DIR = "/app/data/files212/welcome_menu/example_photo"
FILE_ID_PATH = "/app/data/files212/welcome_menu/files_id/files_id.txt"
EXAMPLE_PAGES = 10

def load_file_ids(filepath):
    file_ids = {}
    log_event("load_file_ids_called", filepath=filepath)
    if not os.path.exists(filepath):
        log_event("file_ids_file_not_found", filepath=filepath)
        return file_ids
    try:
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line or " - " not in line:
                    continue
                name, file_id = line.split(" - ", 1)
                file_ids[name.strip()] = file_id.strip()
        log_event("file_ids_loaded", count=len(file_ids))
    except Exception as e:
        log_event("file_ids_load_error", error=str(e))
    return file_ids

def save_file_ids(filepath, file_ids_dict):
    try:
        with open(filepath, "w") as f:
            for fname, file_id in file_ids_dict.items():
                f.write(f"{fname} - {file_id}\n")
        log_event("file_ids_saved", count=len(file_ids_dict))
    except Exception as e:
        log_event("file_ids_save_error", error=str(e))

def get_example_keyboard(page):
    prev_btn = InlineKeyboardButton("◀️", callback_data="example_prev") if page > 1 else None
    next_btn = InlineKeyboardButton("▶️", callback_data="example_next") if page < EXAMPLE_PAGES else None
    row = [btn for btn in [prev_btn, next_btn] if btn]
    keyboard = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("Пропустить", callback_data="example_skip")])
    return InlineKeyboardMarkup(keyboard)

async def show_example_page(context, chat_id, page=1, edit=False, message_id=None):
    """Отправляет или редактирует пример работы. Возвращает msg при send_photo, иначе None."""
    user_id = chat_id
    file_ids = load_file_ids(FILE_ID_PATH)
    fname = f"{page}.png"
    file_id = file_ids.get(fname)
    caption = f"Пример работы. Страница: {page}/10."
    log_event("show_example_page_called", chat_id=chat_id, user_id=user_id, page=page, edit=edit, file_id_found=bool(file_id))

    need_new_file = False

    if file_id:
        try:
            if edit and message_id is not None:
                await context.bot.edit_message_media(
                    media=InputMediaPhoto(media=file_id, caption=caption),
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=get_example_keyboard(page)
                )
                log_event("edit_message_media_by_file_id_success", chat_id=chat_id, file_id=file_id, page=page)
                return None
            else:
                msg = await context.bot.send_photo(chat_id=chat_id, photo=file_id, caption=caption, reply_markup=get_example_keyboard(page))
                log_event("send_photo_by_file_id_success", chat_id=chat_id, file_id=file_id, page=page)
                return msg
        except Exception as e:
            need_new_file = True
            log_event("file_id_invalid_or_send_error", file_id=file_id, error=str(e), page=page)
    else:
        need_new_file = True

    if need_new_file:
        file_path = os.path.join(EXAMPLE_DIR, fname)
        if not os.path.exists(file_path):
            log_event("example_file_not_found", file_path=file_path, chat_id=chat_id, page=page)
            await context.bot.send_message(chat_id=chat_id, text="Файл с примером не найден.")
            return None
        with open(file_path, "rb") as photo:
            try:
                if edit and message_id is not None:
                    await context.bot.edit_message_media(
                        media=InputMediaPhoto(media=photo, caption=caption),
                        chat_id=chat_id,
                        message_id=message_id,
                        reply_markup=get_example_keyboard(page)
                    )
                    log_event("edit_message_media_by_file_success", chat_id=chat_id, file_path=file_path, page=page)
                    return None
                else:
                    msg = await context.bot.send_photo(chat_id=chat_id, photo=photo, caption=caption, reply_markup=get_example_keyboard(page))
                    log_event("send_photo_by_file_success", chat_id=chat_id, file_path=file_path, page=page)
                    try:
                        new_file_id = (msg.photo[-1].file_id if hasattr(msg, "photo") and msg.photo else None)
                    except Exception as e:
                        new_file_id = None
                        log_event("extract_file_id_error", error=str(e))
                    if new_file_id:
                        file_ids[fname] = new_file_id
                        save_file_ids(FILE_ID_PATH, file_ids)
                        log_event("new_file_id_saved", file_name=fname, file_id=new_file_id)
                    return msg
            except Exception as e:
                log_event("send_photo_by_file_error", file_path=file_path, error=str(e), page=page)
                await context.bot.send_message(chat_id=chat_id, text="Ошибка отправки файла с примером.")
                return None

async def show_welcome_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id if update.effective_user else "unknown"
    log_event("show_welcome_menu", chat_id=chat_id, user_id=user_id)
    await context.bot.send_message(
        chat_id=chat_id,
        text=WELCOME_TEXT,
        reply_markup=WELCOME_MENU
    )
    context.user_data["welcome_step"] = "hello"

async def welcome_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    step = query.data
    chat_id = query.message.chat_id
    user_id = query.from_user.id if query.from_user else "unknown"
    log_event("welcome_menu_callback_called", step=step, chat_id=chat_id, user_id=user_id)
    await query.answer()

    if step == "welcome_cost":
        log_event("show_cost", chat_id=chat_id)
        await query.edit_message_text(COST_TEXT, reply_markup=COST_MENU)
        context.user_data["welcome_step"] = "cost"
    elif step == "welcome_pay":
        log_event("show_pay", chat_id=chat_id)
        await query.edit_message_text(PAY_TEXT, reply_markup=PAY_MENU)
        context.user_data["welcome_step"] = "pay"
    elif step == "welcome_ref":
        log_event("show_ref", chat_id=chat_id)
        await query.edit_message_text(REF_TEXT, reply_markup=REF_MENU)
        context.user_data["welcome_step"] = "ref"
    elif step == "welcome_back_to_hello":
        log_event("back_to_hello", chat_id=chat_id)
        await query.edit_message_text(WELCOME_TEXT, reply_markup=WELCOME_MENU)
        context.user_data["welcome_step"] = "hello"

    elif step == "welcome_start":
        log_event("start_example", chat_id=chat_id)
        context.user_data["welcome_step"] = "example"
        context.user_data["example_page"] = 1
        # Удаляем сообщение с рефералкой
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=query.message.message_id)
            log_event("ref_message_deleted", chat_id=chat_id, msg_id=query.message.message_id)
        except Exception as e:
            log_event("ref_message_delete_error", chat_id=chat_id, msg_id=query.message.message_id, error=str(e))
        # Отправляем первое фото с примером работы и сохраняем message_id для дальнейших редактирований
        msg = await show_example_page(context, chat_id, page=1, edit=False, message_id=None)
        if msg:
            context.user_data["example_message_id"] = msg.message_id

    elif step == "example_prev":
        page = context.user_data.get("example_page", 1)
        page = max(1, page - 1)
        context.user_data["example_page"] = page
        message_id = context.user_data.get("example_message_id")
        await show_example_page(context, chat_id, page=page, edit=True, message_id=message_id)
    elif step == "example_next":
        page = context.user_data.get("example_page", 1)
        page = min(EXAMPLE_PAGES, page + 1)
        context.user_data["example_page"] = page
        message_id = context.user_data.get("example_message_id")
        await show_example_page(context, chat_id, page=page, edit=True, message_id=message_id)
    elif step == "example_skip":
        log_event("example_skip", chat_id=chat_id)
        from bot import start  # или корректно импортируй из bot
        await start(update, context)
        context.user_data["welcome_step"] = "hello"
    else:
        log_event("fallback", chat_id=chat_id)
        await query.edit_message_text(WELCOME_TEXT, reply_markup=WELCOME_MENU)
        context.user_data["welcome_step"] = "hello"
