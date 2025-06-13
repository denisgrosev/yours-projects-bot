import logging
from telegram import Update
from telegram.ext import ContextTypes
from balance_utils import (
    set_user_balance, 
    add_user_balance, 
    minus_user_balance, 
    get_user_balance,
    update_user_info,
    find_user_id_by_username
)

ADMIN_IDS = [5236886477]

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def resolve_user_id(context, user_arg: str):
    if user_arg.startswith('@'):
        username = user_arg.lstrip("@").strip()
        user_id = find_user_id_by_username(username)
        if user_id:
            print(f"DEBUG: найден user_id={user_id} по username @{username} (локально)")
        else:
            print(f"DEBUG: username @{username} не найден в базе")
        return user_id
    else:
        try:
            return int(user_arg.strip())
        except ValueError:
            return None

async def set_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Обновить username в базе при любом сообщении
    user = update.effective_user
    update_user_info(user.id, user.username)
    if not is_admin(user.id):
        await update.message.reply_text("Команда не найдена")
        return
    if len(context.args) != 2:
        await update.message.reply_text("Формат: /set_balance @username сумма или /set_balance user_id сумма")
        return
    user_arg, amount = context.args
    user_id = await resolve_user_id(context, user_arg)
    if not user_id:
        await update.message.reply_text("Пользователь не найден в базе. Пусть напишет боту /start.")
        return
    set_user_balance(user_id, float(amount))
    user_label = user_arg if user_arg.startswith('@') else f"id {user_id}"
    await update.message.reply_text(f"Баланс пользователя {user_label} установлен на {amount}")

async def plus_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    update_user_info(user.id, user.username)
    if not is_admin(user.id):
        await update.message.reply_text("Команда не найдена")
        return
    if len(context.args) != 2:
        await update.message.reply_text("Формат: /plus_balance @username сумма или /plus_balance user_id сумма")
        return
    user_arg, amount = context.args
    user_id = await resolve_user_id(context, user_arg)
    if not user_id:
        await update.message.reply_text("Пользователь не найден в базе. Пусть напишет боту /start.")
        return
    add_user_balance(user_id, float(amount))
    user_label = user_arg if user_arg.startswith('@') else f"id {user_id}"
    await update.message.reply_text(f"Пользователю {user_label} добавлено {amount}")

async def minus_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    update_user_info(user.id, user.username)
    if not is_admin(user.id):
        await update.message.reply_text("Команда не найдена")
        return
    if len(context.args) != 2:
        await update.message.reply_text("Формат: /minus_balance @username сумма или /minus_balance user_id сумма")
        return
    user_arg, amount = context.args
    user_id = await resolve_user_id(context, user_arg)
    if not user_id:
        await update.message.reply_text("Пользователь не найден в базе. Пусть напишет боту /start.")
        return
    minus_user_balance(user_id, float(amount))
    user_label = user_arg if user_arg.startswith('@') else f"id {user_id}"
    await update.message.reply_text(f"У пользователя {user_label} отнято {amount}")

async def user_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    update_user_info(user.id, user.username)
    if not is_admin(user.id):
        await update.message.reply_text("Команда не найдена")
        return
    if len(context.args) != 1:
        await update.message.reply_text("Формат: /user_balance @username или /user_balance user_id")
        return
    user_arg = context.args[0]
    user_id = await resolve_user_id(context, user_arg)
    if not user_id:
        await update.message.reply_text("Пользователь не найден в базе. Пусть напишет боту /start.")
        return
    balance = get_user_balance(user_id)
    user_label = user_arg if user_arg.startswith('@') else f"id {user_id}"
    await update.message.reply_text(f"Баланс пользователя {user_label}: {balance}")