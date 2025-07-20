from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes

WELCOME_TEXT = (
    "Привет! Это бот «Твои проекты🖨️», который автоматически создаёт учебные работы (курсовые, доклады, рефераты) по вашей теме и предмету. Забудьте о бессонных ночах — бот всё сделает быстро и качественно."
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
    "– Приглашайте друзей и получайте 20 % от каждого их пополнения.\n"
    "– Бонусы мгновенно зачисляются на ваш основной баланс.\n"
    "– Реферальные деньги можно вывести на банковскую карту или перевести в баланс для новых заказов.\n"
    "– Свою ссылку и статистику приглашений смотрите в разделе «Реферальная система»."
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

    # Навигация между меню
    if step == "welcome_cost":
        await query.edit_message_text(COST_TEXT, reply_markup=COST_MENU)
        context.user_data["welcome_step"] = "cost"
    elif step == "welcome_pay":
        await query.edit_message_text(PAY_TEXT, reply_markup=PAY_MENU)
        context.user_data["welcome_step"] = "pay"
    elif step == "welcome_ref":
        await query.edit_message_text(REF_TEXT, reply_markup=REF_MENU)
        context.user_data["welcome_step"] = "ref"
    elif step == "welcome_start":
        from bot import start  # или импортируй корректно
        await start(update, context)  # Перекидываем в основное меню
    elif step == "welcome_back_to_hello":
        await query.edit_message_text(WELCOME_TEXT, reply_markup=WELCOME_MENU)
        context.user_data["welcome_step"] = "hello"
    elif step == "welcome_cost":
        await query.edit_message_text(COST_TEXT, reply_markup=COST_MENU)
        context.user_data["welcome_step"] = "cost"
    elif step == "welcome_pay":
        await query.edit_message_text(PAY_TEXT, reply_markup=PAY_MENU)
        context.user_data["welcome_step"] = "pay"
    elif step == "welcome_ref":
        await query.edit_message_text(REF_TEXT, reply_markup=REF_MENU)
        context.user_data["welcome_step"] = "ref"
    elif step == "welcome_cost":
        await query.edit_message_text(COST_TEXT, reply_markup=COST_MENU)
        context.user_data["welcome_step"] = "cost"
    else:
        await query.edit_message_text(WELCOME_TEXT, reply_markup=WELCOME_MENU)
        context.user_data["welcome_step"] = "hello"
