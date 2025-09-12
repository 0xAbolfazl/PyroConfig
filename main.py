from pip import main
main(['install', 'telethon'])
import logging
import os
import json
import asyncio
from telethon.sessions import StringSession
from telethon.sync import TelegramClient
from telethon.tl.types import Message, MessageEntityTextUrl, MessageEntityUrl
from telethon.sessions import StringSession
from telethon.errors import ChannelInvalidError, PeerIdInvalidError
from collections import defaultdict
from datetime import timedelta, datetime
import re

SESSION = os.getenv('SESSION_STRING')
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
CHANNELS = 'channels.json'
LOGS = 'logs.txt'
CONFIG_FOLDER = 'Configs'

CONFIG_PATTERNS = {
    "vless": r"vless://[^\s]+",
    "vmess": r"vmess://[^\s]+",
    "shadowsocks": r"ss://[^\s]+",
    "trojan": r"trojan://[^\s]+"
}
PROXY_PATTERN = r"https:\/\/t\.me\/proxy\?server=[^&\s\)]+&port=\d+&secret=[^\s\)]+"

if not os.path.exists(CONFIG_FOLDER):
    os.makedirs(CONFIG_FOLDER)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.handlers = []
file_handler = logging.FileHandler('logs.txt', mode='w', encoding='utf-8')
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)

def load_channels():
    '''
    Return channel list
    '''
    with open(CHANNELS, 'r') as ch:
        channels_list = json.load(ch)['all_channels']
        logger.info(f'{len(channels_list)} Channels Loaded !')
        return channels_list
    
async def fetch_configs(client, channel):
    pass

def fetch_proxies():
    pass

def save_configs():
    pass

def post_configs():
    pass

async def main():
    logger.info("Starting main function")
    
    TELEGRAM_CHANNELS = load_channels()
    session = StringSession(SESSION)

    try:
        async with TelegramClient(session, API_ID, API_HASH) as client:
            if not await client.is_user_authorized():
                logger.error("Invalid session")
                print("Invalid session")
                return

            for channel in TELEGRAM_CHANNELS:
                logger.info(f"Fetching configs/proxies from {channel}...")
                print(f"Fetching configs/proxies from {channel}...")
                try:
                    channel_configs, is_valid = await fetch_configs(client, channel)
                    if not is_valid:
                        print(f'invalid channel : {channel}')

                    print('this is channel configs : ')
                    print(channel_configs)

                except Exception as e:
                    print('Error in channel loop')
                    print(str(e))

    except Exception as e:
        logger.error(f"Error in main loop: {str(e)}")
        print(f"Error in main loop: {str(e)}")
        return

    logger.info("Config+proxy collection process completed")

if __name__ == "__main__":
    asyncio.run(main())