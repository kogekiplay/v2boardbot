import logging
import os

import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, Dice
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler, MessageHandler, filters,
)

from MenuHandle import *
from MyCommandHandler import *
from Utils import slot_machine
from keyboard import start_keyboard
from v2board import _bind, _checkin, _traffic, _lucky, _addtime
from models import Db, BotDb, BotUser
from config import TOKEN, HTTP_PROXY, HTTPS_PROXY, ADMIN_TELEGRAM_ID, TITLE
from Utils import START_ROUTES, END_ROUTES

# 设置代理，如果在国内需要设置，如果在国外就不需要设置，注释即可
if HTTP_PROXY:
    os.environ['HTTP_PROXY'] = HTTP_PROXY
if HTTPS_PROXY:
    os.environ['HTTPS_PROXY'] = HTTPS_PROXY

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_TELEGRAM_ID and update.effective_message.chat.type == 'private':
        start_keyboard_admin = [
            InlineKeyboardButton(text='⏱添加时长', callback_data='addtime'),
            InlineKeyboardButton(text='🔁重置流量', callback_data='resetdata')
        ]
        start_keyboard_copy = start_keyboard.copy()
        start_keyboard_copy.append(start_keyboard_admin)
        reply_markup = InlineKeyboardMarkup(start_keyboard_copy)
    else:
        reply_markup = InlineKeyboardMarkup(start_keyboard)
    # await context.bot.send_message(chat_id=update.effective_chat.id, text='my Bot', reply_markup=reply_markup)
    await update.message.reply_text(TITLE, reply_markup=reply_markup)
    return START_ROUTES


async def start_over(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    reply_markup = InlineKeyboardMarkup(start_keyboard)
    # await context.bot.send_message(chat_id=update.effective_chat.id, text='my Bot', reply_markup=reply_markup)
    await query.edit_message_text(TITLE, reply_markup=reply_markup)
    return START_ROUTES


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="欢迎下次光临！")
    return ConversationHandler.END


# 获取电报id
async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_user.id, text=update.effective_chat.id)


async def handle_input_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    try:
        text = _addtime(int(user_input))
    except:
        text = '输入有误，请输入整数'
    await update.message.reply_text(text)
    return ConversationHandler.END


async def quit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('已退出输入模式')
    return ConversationHandler.END


if __name__ == '__main__':
    # 面板数据库连接
    Db.connect()
    if os.path.exists('bot.db'):
        res = BotDb.connect()
    else:
        res = BotDb.connect()
        BotDb.create_tables([BotUser])

    application = Application.builder().token(TOKEN).build()
    CommandList = [
        CommandHandler("start", start),
        CommandHandler("myid", myid),
        CommandHandler("checkin", command_checkin),  # 处理签到命令
        CommandHandler('bind', command_bind),  # 处理绑定命令
        CommandHandler('unbind', command_unbind),  # 处理解绑命令
        CommandHandler('lucky', command_lucky),  # 处理幸运抽奖命令
        CommandHandler('wallet', command_wallet),  # 处理查看钱包命令
        CommandHandler('traffic', command_traffic),  # 处理查看流量命令

    ]
    conv_handler = ConversationHandler(
        entry_points=CommandList,
        states={
            START_ROUTES: [
                CallbackQueryHandler(menu_addtime, pattern="^addtime"),
                CallbackQueryHandler(menu_slot_machine, pattern="^slot_machine"),
                CallbackQueryHandler(menu_wallet, pattern="^wallet"),
                CallbackQueryHandler(menu_checkin, pattern="^checkin$"),
                CallbackQueryHandler(menu_sub, pattern="^sub$"),
                CallbackQueryHandler(menu_mysub, pattern="^mysub"),
                CallbackQueryHandler(menu_traffic, pattern="^traffic$"),
                CallbackQueryHandler(menu_lucky, pattern="^lucky"),
                CallbackQueryHandler(menu_node, pattern="^node"),
                CallbackQueryHandler(start_over, pattern="^start_over$"),
                CallbackQueryHandler(end, pattern="^end$"),
                # CallbackQueryHandler(three, pattern="^" + str(THREE) + "$"),
                # CallbackQueryHandler(four, pattern="^" + str(FOUR) + "$"),
            ],
            WAITING_INPUT: [
                MessageHandler(filters.Text(['不玩了', '退出', 'quit']), quit_input),
                MessageHandler(filters.Dice(), slot_machine),
            ],
            'addtime': [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input_text)
            ]
        },
        fallbacks=CommandList,
    )

    application.add_handler(conv_handler)

    # 异步运行
    application.run_polling()

    # 关闭数据库
    Db.close()
    BotDb.close()

    # 命令处理
    # start_handler = CommandHandler('start', start)
    # bind_handler = CommandHandler('bind', bind)  # 处理绑定命令
    # checkin_handler = CommandHandler('checkin', checkin)  # 处理签到命令
    # traffic_handler = CommandHandler('traffic', traffic)  # 处理查看流量命令
    # lucky_handler = CommandHandler('lucky', lucky)  # 处理抽奖命令

    # 消息处理

    # 添加处理插件
    # application.add_handler(start_handler)
    # application.add_handler(bind_handler)  # 添加绑定处理方法
    # application.add_handler(checkin_handler)  # 添加签到处理方法
    # application.add_handler(traffic_handler)  # 添加查看流量处理方法
    # application.add_handler(lucky_handler)  # 添加抽奖处理方法
