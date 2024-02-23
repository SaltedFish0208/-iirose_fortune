import json
import random
import os

from loguru import logger
from PIL import Image, ImageDraw, ImageFont
from typing import List, Optional, Tuple
from pathlib import Path
from API.api_message import at_user
from API.api_iirose import APIIirose  # 大部分接口都在这里
from globals.globals import GlobalVal  # 一些全局变量 now_room_id 是机器人当前所在的房间标识，websocket是ws链接，请勿更改其他参数防止出bug，也不要去监听ws，websockets库只允许一个接收流
from API.api_get_config import get_master_id  # 用于获取配置文件中主人的唯一标识
from API.decorator.command import on_command, MessageType  # 注册指令装饰器和消息类型Enmu

API = APIIirose()  # 吧class定义到变量就不会要求输入self了（虽然我都带了装饰器没有要self的 直接用APIIirose也不是不可以 习惯了
with open('./plugins/iirose_fortune/copywriting.json', 'r') as f:
    cw = json.load(f)

with open('./plugins/iirose_fortune/piclist.json', 'r') as f:
    piclist = json.load(f)

def decrement(text: str) -> Tuple[int, List[str]]:
    """
    Split the text, return the number of columns and text list
    TODO: Now, it ONLY fit with 2 columns of text
    """
    length: int = len(text)
    result: List[str] = []
    cardinality = 9
    if length > 4 * cardinality:
        raise Exception

    col_num: int = 1
    while length > cardinality:
        col_num += 1
        length -= cardinality

    # Optimize for two columns
    space = " "
    length = len(text)  # Value of length is changed!

    if col_num == 2:
        if length % 2 == 0:
            # even
            fillIn = space * int(9 - length / 2)
            return col_num, [
                text[: int(length / 2)] + fillIn,
                fillIn + text[int(length / 2) :],
            ]
        else:
            # odd number
            fillIn = space * int(9 - (length + 1) / 2)
            return col_num, [
                text[: int((length + 1) / 2)] + fillIn,
                fillIn + space + text[int((length + 1) / 2) :],
            ]

    for i in range(col_num):
        if i == col_num - 1 or col_num == 1:
            result.append(text[i * cardinality :])
        else:
            result.append(text[i * cardinality : (i + 1) * cardinality])

    return col_num, result

def drawpic(Message, luck, text):
    theme = random.choice(list(piclist.keys()))
    bgpic = random.choice(piclist.get(theme))
    imgdir = "./plugins/iirose_fortune/img/"
    background = Image.open(f'{imgdir}/{theme}/{bgpic}')
    draw = ImageDraw.Draw(background)

    font_size = 45
    color = "#F5F5F5"
    image_font_center = [140, 99]
    fontPath = {
        "title": "./plugins/iirose_fortune/font/Mamelon.otf",
        "text": "./plugins/iirose_fortune//font/sakura.ttf",
    }
    ttfront = ImageFont.truetype(fontPath["title"], font_size)
    font_length = ttfront.getbbox(luck)
    draw.text(
        (
            image_font_center[0] - font_length[2] / 2,
            image_font_center[1] - font_length[3] / 2,
        ),
        luck,
        fill=color,
        font=ttfront,
    )

    font_size = 25
    color = "#323232"
    image_font_center = [140, 297]
    ttfront = ImageFont.truetype(fontPath["text"], font_size)
    slices, result = decrement(text)

    for i in range(slices):
        font_height: int = len(result[i]) * (font_size + 4)
        textVertical: str = "\n".join(result[i])
        x: int = int(
            image_font_center[0]
            + (slices - 2) * font_size / 2
            + (slices - 1) * 4
            - i * (font_size + 4)
        )
        y: int = int(image_font_center[1] - font_height / 2)
        draw.text((x, y), textVertical, fill=color, font=ttfront)

    
    outDir = Path("/root/iirosebot/iirosebot-1.4.5/out/")
    if not outDir.exists():
        outDir.mkdir(exist_ok=True, parents=True)
    outPath = outDir / f"{Message.user_name}.png"
    filename=f"{Message.user_name}.png"
    background.save(outPath)
    return outPath



@on_command('>今日运势', False, command_type=[MessageType.room_chat, MessageType.private_chat])  # command_type 参数可让本指令在哪些地方生效，发送弹幕需验证手机号，每天20条。本参数需要输入列表，默认不输入的情况下只对房间消息做出反应，单个类型也需要是列表
async def fortune(Message):
    lucky = random.choice(list(cw.keys()))
    text = random.choice(cw.get(lucky))
    pic = drawpic(Message, lucky, text)
    await API.send_msg(Message, f'{at_user(Message.user_name)}\n'
                                f'{await API.upload_files(pic)}#e')
    os.remove(pic)

async def user_move_room(Message):
    # 当房间内非机器人用户移动到其他房间时触发本函数
    pass


async def user_join_room(Message):
    # 当有用户(包括机器人)加入到当前房间时触发本函数
    # 框架默认消息均不排除自身，请通过Message中的is_bot进行判断，该参数为布朗类，为True时说明该消息为自身
    pass


async def user_leave_room(Message):
    # 当有用户(包括机器人)离开到当前房间时触发本函数
    # 接口内还有其他参数可根据注释自行使用，如有疑问请加入README中的房间询问
    pass



async def revoke_message(Message):
    # 有撤回消息时会触发这个函数（不排除自身
    # Message里面只有user_id和message_id
    pass


async def on_init():
    logger.info('框架会在收到机器人加入房间的消息后执行这个函数，只会执行一次')  # 本框架使用logger日志管理器
