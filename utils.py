import random
import string
from database import (
    save_file as db_save_file,
    get_files as db_get_files,
    increment_downloads as db_inc_downloads,
    get_download_count as db_get_dl_count,
    add_channel,
    remove_channel,
    get_required_channels
)
from telegram import ChatMember


def gen_code(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def save_file(file_id, code):
    db_save_file(file_id, code)


def get_files(code):
    return db_get_files(code)


def increase_downloads(code):
    db_inc_downloads(code)


def get_download_count(code):
    return db_get_dl_count(code)


def add_required_channel(username):
    add_channel(username)


def remove_required_channel(username):
    remove_channel(username)


def list_required_channels():
    return get_required_channels()


async def is_user_member(bot, user_id, channel_username):
    try:
        member = await bot.get_chat_member(chat_id=f"@{channel_username}", user_id=user_id)
        return member.status in [ChatMember.MEMBER, ChatMember.OWNER, ChatMember.ADMINISTRATOR]
    except:
        return False


async def check_user_membership(bot, user_id):
    not_joined = []
    channels = list_required_channels()
    for ch in channels:
        if not await is_user_member(bot, user_id, ch):
            not_joined.append(ch)
    return not_joined
