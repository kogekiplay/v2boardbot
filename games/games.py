from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from Config import config
from Utils import START_ROUTES
from games.utils import get_traffic, edit_traffic
from keyboard import return_keyboard
from models import V2User, BotUser
from functools import wraps
import asyncio, logging
import random


def auto_delete_required(func):
    # 用functools.wraps来保留原函数的属性和文档
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 检查auto_delete的值
        if config.AUTODELETE.switch:
            return func(*args, **kwargs)
        else:
            pass

    return wrapper

@auto_delete_required
async def delete_both_messages(update, context):
    # 获取用户消息的id和chat id
    user_message_id = update.message.message_id
    user_chat_id = update.message.chat_id
    # 获取bot在当前聊天中的状态
    bot_status = await context.bot.get_chat_member(
        chat_id=user_chat_id, user_id=context.bot.id
    )
    # 判断bot是否是管理员或者拥有者
    if bot_status.status in ['administrator', 'creator']:
        # 判断bot是否有删除消息的权限
        if bot_status.can_delete_messages:
            # 获取bot消息的id和chat id
            bot_message_id = context.bot_data["bot_message_id"]
            bot_chat_id = context.bot_data["bot_chat_id"]
            # 创建一个空列表
            messages_to_delete = []
            # 将用户和 bot 的消息加入列表
            messages_to_delete.append(context.bot.delete_message(
                            chat_id=user_chat_id, message_id=user_message_id
                        ))
            messages_to_delete.append(context.bot.delete_message(chat_id=bot_chat_id, message_id=bot_message_id))
            # 判断骰子消息的 id 和 chat id 是否存在
            if "dice_message_id" in context.bot_data and "dice_chat_id" in context.bot_data:
                # 如果存在，就将骰子消息加入列表
                messages_to_delete.append(context.bot.delete_message(
                                chat_id=context.bot_data["dice_chat_id"],
                                message_id=context.bot_data["dice_message_id"],
                        ))
            # 如果有，就等待5秒
            await asyncio.sleep(5)
            # 同时删除用户和bot的消息
            await asyncio.gather(*messages_to_delete)
        else:
            # 如果没有，就打印一个警告信息
            logging.warning(
                f"Warning: Bot does not have permission to delete messages in chat {user_chat_id}"
            )
    else:
        # 如果不是管理员或者拥有者，就跳过这一步
        pass

# 判断是否转发消息
async def is_forward(update: Update, context: ContextTypes.DEFAULT_TYPE, v2_user, bot_user):
    if update.message.forward_from or update.message.forward_sender_name:
        result = f'由于你想投机取巧，因此没收你的下注流量!\n不和没有诚信的人玩，游戏结束!\n当前账户流量：{await edit_traffic(v2_user, bot_user.betting)}GB'
        return result
    else:
        return False


# 判断能否流量是否够玩游戏
async def can_games(v2_user, bot_user):
    traffic = await get_traffic(v2_user)
    if traffic < bot_user.betting:
        return f'你的流量已不足{bot_user.betting}G，无法进行游戏'
    else:
        return True


async def tiger(update: Update, context: ContextTypes.DEFAULT_TYPE, v2_user, bot_user):
    # 开关
    if config.TIGER.switch != True:
        return '当前老虎机游戏关闭，不可进行游戏', START_ROUTES

    # 判断能否玩游戏
    can_game = await can_games(v2_user, bot_user)
    if can_game != True:
        return can_game, ConversationHandler.END

    # 判断是否转发
    forward = await is_forward(update, context, v2_user, bot_user)
    if forward == False:
        # 扣下注流量
        traffic = await edit_traffic(v2_user, -bot_user.betting)
        rate = config.TIGER.rate * bot_user.betting
        if update.message.dice.value in [1, 22, 43, 64]:
            # 中奖
            result = f'恭喜你中奖了，获得{rate}GB流量已经存入你的账户\n当前账户流量：{await edit_traffic(v2_user, rate)}GB'
        else:
            # 没中奖
            result = f'很遗憾你没有中奖，流量已从你账户扣除{bot_user.betting}GB\n当前账户流量：{traffic}GB'
        return result, START_ROUTES
    else:
        return forward, ConversationHandler.END


async def dice_(update: Update, context: ContextTypes.DEFAULT_TYPE, v2_user, bot_user):
    # 开关
    if config.DICE.switch != True:
        return '当前骰子游戏关闭，不可进行游戏', START_ROUTES

    # 判断能否玩游戏
    can_game = await can_games(v2_user, bot_user)
    if can_game != True:
        return can_game, ConversationHandler.END

    # 判断是否转发
    forward = await is_forward(update, context, v2_user, bot_user)
    if forward == False:
        # 设置最小和最大下注流量
        maxnum=round(v2_user.transfer_enable / 1024 ** 3 * 0.25, 2)
        max_betting = min(maxnum, bot_user.betting)
        print(bot_user.betting)
        print(max_betting)
        if bot_user.betting < 1 or bot_user.betting > max_betting:
            return f'下注流量必须在1GB到{max_betting}GB之间', START_ROUTES
        
        # 扣下注流量
        traffic = await edit_traffic(v2_user, -bot_user.betting)
        # 如果中奖获得的流量
        rate = config.DICE.rate * bot_user.betting

        user = update.message.dice.value
        bot_message = await update.message.reply_dice(emoji='🎲')
        # 保存bot发出的骰子消息的id和chat id到context.bot_data中
        context.bot_data["dice_message_id"] = bot_message.message_id
        context.bot_data["dice_chat_id"] = bot_message.chat_id
        # 调用delete_both_messages函数来删除用户和bot的消息
        asyncio.get_event_loop().create_task(delete_both_messages(update, context))
        bot = bot_message.dice.value
        if user > bot:
            # 中奖
            result = f'恭喜你中奖了，获得{rate}GB流量已经存入你的账户\n当前账户流量：{await edit_traffic(v2_user, rate)}GB'
        elif user == bot:
            # 平局
            traffic = await edit_traffic(v2_user, bot_user.betting)
            result = f'平局，已返还下注流量\n当前账户流量：{traffic}GB'
        else:
            # 没中奖
            result = f'很遗憾你没有中奖，流量已从你账户扣除{bot_user.betting}GB\n当前账户流量：{traffic}GB'
        return result, START_ROUTES
    else:
        return forward, ConversationHandler.END


# 用户退出游戏
async def quit_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    keyboard = [
        return_keyboard,
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot_user = BotUser.select().where(BotUser.telegram_id == telegram_id).first()
    if not bot_user:
        await update.message.reply_text('未绑定,请先绑定\n使用 /bind 命令绑定你的订阅', reply_markup=reply_markup)
        return START_ROUTES
    bot_user.is_game = False
    bot_user.save()
    await update.message.reply_text('已退出赌博模式。', reply_markup=reply_markup)
    return START_ROUTES


async def select_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    query = update.callback_query
    if query:
        await query.answer()
        betting = update.callback_query.data
    else:
        betting = update.message.text + 'GB'
        query = update


    if betting == 'xGB':
        await query.message.reply_text(text=f'请发送你要下注的流量，单位：GB')
        return 'input_betting'
    bot_user = BotUser.select().where(BotUser.telegram_id == telegram_id).first()
    try:
        bot_user.betting = int(betting.replace('GB', ''))
        bot_user.save()
        await query.message.reply_text(text=f'下注成功，你每局游戏将下注{betting}流量')
    except ValueError:
        # 如果出现异常，就捕获它，并给用户发送一条消息
        await update.message.reply_text(text=f'输入有误，请输入一个数字')
    return START_ROUTES


# 用户开始游戏
async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    keyboard = [[], []]
    for i in range(1, 11):
        if i < 6:
            keyboard[0].append(InlineKeyboardButton(f'{i}GB', callback_data=f'{i}GB'))
        else:
            keyboard[1].append(InlineKeyboardButton(f'{i}GB', callback_data=f'{i}GB'))

    keyboard.append([InlineKeyboardButton(f'自定义下注流量', callback_data=f'xGB')])
    keyboard.append(return_keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    await query.answer()

    v2_user = V2User.select().where(V2User.telegram_id == telegram_id).first()
    if not v2_user:
        await update.message.reply_text(
            text=f'未绑定,请先绑定\n使用 /bind 命令绑定你的订阅',
            reply_markup=reply_markup
        )
        return START_ROUTES

    if config.GAME.switch != True:
        await update.message.reply_text(text='当前赌博模式关闭，请联系管理员！')
        return ConversationHandler.END

    bot_user = BotUser.select().where(BotUser.telegram_id == telegram_id).first()
    bot_user.is_game = True
    bot_user.save()
    await query.edit_message_text(
        text=f'当前赔率:🎰1赔{config.TIGER.rate}   🎲1赔{config.DICE.rate}\n发送"不玩了"退出赌博模式\n请选择下注流量或自定义：',
        reply_markup=reply_markup
    )
    return START_ROUTES


async def gambling(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    keyboard = [
        return_keyboard,
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    v2_user = V2User.select().where(V2User.telegram_id == telegram_id).first()
    if not v2_user:
        await update.message.reply_text(
            text=f'未绑定,请先绑定\n使用 /bind 命令绑定你的订阅',
            reply_markup=reply_markup
        )
        return START_ROUTES

    if config.GAME.switch != True:
        await update.message.reply_text(text='当前赌博模式关闭，请联系管理员！')
        return ConversationHandler.END

    # 判断该用户有没有开启赌博模式
    bot_user = BotUser.select().where(BotUser.telegram_id == telegram_id).first()
    if bot_user.is_game != True:
        keyboard = [
            [InlineKeyboardButton('开启', callback_data='start_game')],
            return_keyboard,
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text='你没有开启赌博模式，是否开启？', reply_markup=reply_markup)
        return START_ROUTES

    result = f'暂不支持{update.message.dice.emoji}玩法。'
    STATUS = START_ROUTES

    # 开始玩游戏
    v2_user = V2User.select().where(V2User.telegram_id == telegram_id).first()
    # 分流
    if update.message.dice.emoji == '🎰':
        result, STATUS = await tiger(update, context, v2_user, bot_user)

    if update.message.dice.emoji == '🎲':
        result, STATUS = await dice_(update, context, v2_user, bot_user)

    bot_message = await update.message.reply_text(text=result)
    # 保存bot消息的id和chat id到context.bot_data中
    context.bot_data["bot_message_id"] = bot_message.message_id
    context.bot_data["bot_chat_id"] = bot_message.chat_id
    if '中奖了' not in result:
        # 调用delete_both_messages函数来删除用户和bot的消息
        asyncio.get_event_loop().create_task(delete_both_messages(update, context))
    else:
        pass
    return STATUS

# 俄罗斯转盘
async def roulette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 开关
    if config.ROULETTE.switch != True:
        bot_message = await update.message.reply_text('当前俄罗斯轮盘游戏关闭，不可进行游戏')
        return ConversationHandler.END
    v2_user = (
        V2User.select().where(V2User.telegram_id == update.effective_user.id).first()
    )

    if not v2_user:
        bot_message = await update.message.reply_text(
            text="未绑定,请先绑定\n使用 /bind 命令绑定你的订阅"
        )
        context.bot_data["bot_message_id"] = bot_message.message_id
        context.bot_data["bot_chat_id"] = bot_message.chat_id
        asyncio.get_event_loop().create_task(delete_both_messages(update, context))
        return START_ROUTES

    traffic = v2_user.transfer_enable / 1024**3
    upload = v2_user.u / 1024**3
    download = v2_user.d / 1024**3
    roulette = config.ROULETTE.bettraffic
    overage = traffic - upload - download

    if overage < roulette:
        bot_message = await update.message.reply_text(text=f"你的流量已不足{roulette}G，无法进行游戏")
        return START_ROUTES

    if update.message.text == "🔫":
        v2_user.transfer_enable -= roulette *1024 ** 3
        v2_user.save()
        # 获取用户的id
        user_id = update.effective_user.id
        # 获取用户的用户名
        user_name = update.effective_user.first_name
        # 获取聊天的id
        chat_id = update.effective_chat.id
        # 如果聊天还没有开始游戏，初始化一个随机数作为子弹位置，并保存在上下文中
        if chat_id not in context.chat_data:
            context.chat_data[chat_id] = {
                'bullet': random.randint(1, 7),
                'count': 0,
                'dead': False,
            }
        # 获取聊天当前的子弹位置和计数
        bullet = context.chat_data[chat_id]['bullet']
        current_count = context.chat_data[chat_id]['count']
        # 计算用户发送🔫表情后的计数
        new_count = current_count + 1
        # 如果新计数等于子弹位置，表示用户没有中弹，设置dead为True，并回复用户
        if new_count == bullet:
            context.chat_data[chat_id]['dead'] = True
            v2_user.transfer_enable += (bullet * roulette) * 1024**3
            v2_user.save()
            bot_message = await update.message.reply_text(
                text=f'{user_name}\n在第{new_count}次没有中弹\n赢得{bullet * roulette}G\n流量当前账户流量：{round(v2_user.transfer_enable / 1024 ** 3, 2)}GB',
            )
            context.chat_data[chat_id]['bullet'] = random.randint(1, 7)
            context.chat_data[chat_id]['count'] = 0
        # 如果新计数小于子弹位置，表示用户中弹并扣除流量
        elif new_count < bullet:
            bot_message = await update.message.reply_text(
                text=f'{user_name}中弹。\n当前已开{new_count}枪。\n流量已从你账户扣除{roulette}GB\n当前账户流量：{round(v2_user.transfer_enable / 1024 ** 3, 2)}GB',
            )
            # 保存bot消息的id和chat id到context.bot_data中
            context.bot_data["bot_message_id"] = bot_message.message_id
            context.bot_data["bot_chat_id"] = bot_message.chat_id
            asyncio.get_event_loop().create_task(delete_both_messages(update, context))
            context.chat_data[chat_id]['count'] = new_count
    else:
        bot_message = await update.message.reply_text(
                text=f'异常错误。。。',
            )
    return START_ROUTES