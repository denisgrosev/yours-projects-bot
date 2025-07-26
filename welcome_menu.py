from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes

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


def load_file_ids(filepath):
    file_ids = {}
    try:
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line or " - " not in line:
                    continue
                name, file_id = line.split(" - ", 1)
                file_ids[name.strip()] = file_id.strip()
    except FileNotFoundError:
        pass
    return file_ids

def save_file_ids(filepath, file_ids_dict):
    with open(filepath, "w") as f:
        for fname, file_id in file_ids_dict.items():
            f.write(f"{fname} - {file_id}\n")

EXAMPLE_DIR = "/app/data/files212/welcome_menu/example_photo"
FILE_ID_PATH = "/app/data/files212/welcome_menu/files_id/files_id.txt"
EXAMPLE_PAGES = 10

def load_file_ids(filepath):
    file_ids = {}
    if not os.path.exists(filepath):
        return file_ids
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or " - " not in line:
                continue
            name, file_id = line.split(" - ", 1)
            file_ids[name.strip()] = file_id.strip()
    return file_ids

def save_file_ids(filepath, file_ids_dict):
    with open(filepath, "w") as f:
        for fname, file_id in file_ids_dict.items():
            f.write(f"{fname} - {file_id}\n")

def get_example_keyboard(page):
    prev_btn = InlineKeyboardButton("◀️", callback_data="example_prev") if page > 1 else None
    next_btn = InlineKeyboardButton("▶️", callback_data="example_next") if page < EXAMPLE_PAGES else None
    row = [btn for btn in [prev_btn, next_btn] if btn]
    keyboard = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("Пропустить", callback_data="example_skip")])
    return InlineKeyboardMarkup(keyboard)

async def show_example_page(update, context, page=1, edit=False):
    chat_id = update.effective_chat.id
    file_ids = load_file_ids(FILE_ID_PATH)
    fname = f"{page}.png"
    file_id = file_ids.get(fname)
    caption = f"Пример работы. Страница: {page}/10."

    # Определяем, нужно ли отправить новый файл и обновить file_id
    need_new_file = False
    message_func = context.bot.send_photo if not edit else context.bot.edit_message_media

    if file_id:
        try:
            if not edit:
                await context.bot.send_photo(chat_id=chat_id, photo=file_id, caption=caption, reply_markup=get_example_keyboard(page))
            else:
                from telegram import InputMediaPhoto
                await context.bot.edit_message_media(
                    media=InputMediaPhoto(media=file_id, caption=caption),
                    chat_id=chat_id,
                    message_id=update.callback_query.message.message_id,
                    reply_markup=get_example_keyboard(page)
                )
            context.user_data["example_page"] = page
            return
        except Exception as e:
            # file_id невалиден — нужно загрузить файл с диска
            need_new_file = True
    else:
        need_new_file = True

    # Если file_id нет или невалиден, отправляем файл с диска и обновляем file_id.txt
    if need_new_file:
        file_path = os.path.join(EXAMPLE_DIR, fname)
        if not os.path.exists(file_path):
            await context.bot.send_message(chat_id=chat_id, text="Файл с примером не найден.")
            return
        with open(file_path, "rb") as photo:
            if not edit:
                msg = await context.bot.send_photo(chat_id=chat_id, photo=photo, caption=caption, reply_markup=get_example_keyboard(page))
            else:
                from telegram import InputMediaPhoto
                msg = await context.bot.edit_message_media(
                    media=InputMediaPhoto(media=photo, caption=caption),
                    chat_id=chat_id,
                    message_id=update.callback_query.message.message_id,
                    reply_markup=get_example_keyboard(page)
                )
        # Получаем file_id и сохраняем
        try:
            new_file_id = (msg.photo[-1].file_id if hasattr(msg, "photo") and msg.photo else msg.media.photo[-1].file_id)
        except Exception:
            new_file_id = None
        if new_file_id:
            file_ids[fname] = new_file_id
            save_file_ids(FILE_ID_PATH, file_ids)
        context.user_data["example_page"] = page


# Подключи этот обработчик в главном файле и вызови из start() если пользователь новый!
async def show_welcome_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=WELCOME_TEXT,
        reply_markup=WELCOME_MENU
    )
    context.user_data["welcome_step"] = "hello"

async def welcome_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    step = query.data
    await query.answer()

    # Базовые шаги
    if step == "welcome_cost":
        await query.edit_message_text(COST_TEXT, reply_markup=COST_MENU)
        context.user_data["welcome_step"] = "cost"
    elif step == "welcome_pay":
        await query.edit_message_text(PAY_TEXT, reply_markup=PAY_MENU)
        context.user_data["welcome_step"] = "pay"
    elif step == "welcome_ref":
        await query.edit_message_text(REF_TEXT, reply_markup=REF_MENU)
        context.user_data["welcome_step"] = "ref"
    elif step == "welcome_back_to_hello":
        await query.edit_message_text(WELCOME_TEXT, reply_markup=WELCOME_MENU)
        context.user_data["welcome_step"] = "hello"

    # После "рефералка" — старт показа примера работы
    elif step == "welcome_start":
        context.user_data["welcome_step"] = "example"
        context.user_data["example_page"] = 1
        await show_example_page(update, context, page=1)

    # Перелистывание примера работы
    elif step == "example_prev":
        page = context.user_data.get("example_page", 1)
        page = max(1, page - 1)
        context.user_data["example_page"] = page
        await show_example_page(update, context, page=page, edit=True)
    elif step == "example_next":
        page = context.user_data.get("example_page", 1)
        page = min(EXAMPLE_PAGES, page + 1)
        context.user_data["example_page"] = page
        await show_example_page(update, context, page=page, edit=True)
    elif step == "example_skip":
        from bot import start  # или корректно импортируй из bot
        await start(update, context)
        context.user_data["welcome_step"] = "hello"

    # Фолбэк
    else:
        await query.edit_message_text(WELCOME_TEXT, reply_markup=WELCOME_MENU)
        context.user_data["welcome_step"] = "hello"
