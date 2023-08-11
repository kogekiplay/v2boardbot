from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from keyboard import return_keyboard
from Config import config


async def game_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    game_switch = '🚫赌博模式:关' if config.GAME.switch == True else '🔛赌博模式:开'
    keyboard = [
        [
            InlineKeyboardButton(game_switch, callback_data='game_switch'),
        ],
        [
            InlineKeyboardButton('🎰老虎机', callback_data='game_tiger'),
            InlineKeyboardButton('🎲骰子', callback_data='game_dice'),
            InlineKeyboardButton('🔫俄罗斯转盘', callback_data='game_roulette'),
        ],
        return_keyboard,
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=config.TELEGRAM.title, reply_markup=reply_markup
    )
    return 'game_settings'


async def game_switch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if config.GAME.switch == True:
        config.GAME.switch = False
    else:
        config.GAME.switch = True
    config.save()
    await game_settings(update, context)
    return 'game_settings'


async def game_tiger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    switch = '🚫关闭' if config.TIGER.switch == True else '🔛开启'
    keyboard = [
        [
            InlineKeyboardButton(switch, callback_data='tiger_switch'),
            InlineKeyboardButton(f'📈赔率:{config.TIGER.rate}', callback_data='tiger_rate'),
        ],
        return_keyboard,
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text='老虎机配置', reply_markup=reply_markup
    )
    return 'game_settings'


async def edit_tiger_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        config.TIGER.rate = float(update.message.text)
        config.save()
        text = '编辑成功'
    except:
        text = '发送信息错误，必须是数字'

    await update.message.reply_text(text=text)
    return 'game_settings'


async def tiger_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        return_keyboard,
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=f'请发送赔率，发送10则1赔10\n当前倍率：{config.TIGER.rate}', reply_markup=reply_markup
    )
    return 'tiger_rate'


async def tiger_switch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if config.TIGER.switch == True:
        config.TIGER.switch = False
    else:
        config.TIGER.switch = True
    config.save()
    await game_tiger(update, context)
    return 'game_settings'

async def game_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    switch = '🚫关闭' if config.DICE.switch == True else '🔛开启'
    keyboard = [
        [
            InlineKeyboardButton(switch, callback_data='dice_switch'),
            InlineKeyboardButton(f'📈赔率:{config.DICE.rate}', callback_data='dice_rate'),
        ],
        return_keyboard,
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=config.TELEGRAM.title, reply_markup=reply_markup
    )
    return 'game_settings'

async def edit_dice_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        config.DICE.rate = float(update.message.text)
        config.save()
        text = '编辑成功'
    except:
        text = '发送信息错误，必须是数字'

    await update.message.reply_text(text=text)
    return 'game_settings'

async def dice_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        return_keyboard,
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=f'请发送赔率，发送10则1赔10\n当前倍率：{config.DICE.rate}', reply_markup=reply_markup
    )
    return 'dice_rate'

async def dice_switch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if config.DICE.switch == True:
        config.DICE.switch = False
    else:
        config.DICE.switch = True
    config.save()
    await game_dice(update, context)
    return 'game_settings'

async def game_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    switch = '🚫关闭' if config.ROULETTE.switch == True else '🔛开启'
    keyboard = [
        [
            InlineKeyboardButton(switch, callback_data='roulette_switch'),
            InlineKeyboardButton('📈投入流量', callback_data='roulette_bettraffic'),
        ],
        return_keyboard,
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=config.TELEGRAM.title, reply_markup=reply_markup
    )
    return 'game_settings'

async def edit_roulette_bettraffic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        config.ROULETTE.bettraffic = float(update.message.text)
        config.save()
        text = '编辑成功'
    except:
        text = '发送信息错误，必须是数字'

    await update.message.reply_text(text=text)
    return 'game_settings'


async def roulette_bettraffic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        return_keyboard,
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=f'请发送投入的初始流量，发送10则初始10GB\n当前初始流量：{config.ROULETTE.bettraffic}', reply_markup=reply_markup
    )
    return 'roulette_bettraffic'


async def roulette_switch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if config.ROULETTE.switch == True:
        config.ROULETTE.switch = False
        await query.message.reply_text(text='俄罗斯转盘关闭成功')
    else:
        config.ROULETTE.switch = True
        await query.message.reply_text(text='俄罗斯转盘开启成功')
    config.save()
    return 'game_settings'