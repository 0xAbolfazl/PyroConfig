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
from telethon.errors import ChannelInvalidError
from datetime import timedelta, datetime
import re
from typing import List
from urllib.parse import urlparse, parse_qs
from functools import lru_cache

SESSION = os.getenv('SESSION_STRING')
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
CHANNELS = 'channels.json'
LOGS = 'Logs/logs.txt'
CONFIG_FOLDER = 'Configs'
LOGS_FOLDER = 'Logs'
CHANNELS_LOG = 'Logs/channels_log.json'

CONFIG_PATTERNS = {
    "vless": r"vless://[^\s]+",
    "vmess": r"vmess://[^\s]+",
    "shadowsocks": r"ss://[^\s]+",
    "trojan": r"trojan://[^\s]+"
}
PROXY_PATTERN = r'https?://t\.me/proxy\?[^\s]+'

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
    


def extract_proxies_from_message(message) -> List[str]:
    """
    Extrcting proxies from messages
    
    Args:
        message: Telegram message object
    
    Returns:
        List of proxy urls
    """
    proxies = []
    
    if not hasattr(message, 'message') or not message.message:
        return proxies
    
    text = message.message    
    text_proxies = re.findall(PROXY_PATTERN, text)
    proxies.extend(text_proxies)
    
    if hasattr(message, 'entities') and message.entities:
        for entity in message.entities:
            try:
                if isinstance(entity, (MessageEntityTextUrl, MessageEntityUrl)):
                    # extracting url from entities
                    if hasattr(entity, 'url') and entity.url:
                        url = entity.url
                    else:
                        offset = entity.offset
                        length = entity.length
                        if offset + length <= len(text):
                            url = text[offset:offset+length]
                        else:
                            continue
                    
                    # Validating proxies
                    if is_valid_proxy_url(url):
                        proxies.append(url)
                        
            except (IndexError, AttributeError) as e:
                continue
    
    # Deleting duplicate
    return list(dict.fromkeys(proxies)) 

def is_valid_proxy_url(url: str) -> bool:
    """
    Proxy Validating
    
    Args:
        url
    
    Returns:
        bool: True if url is vaild and False if not
    """
    if not url.startswith("https://t.me/proxy?"):
        return False
    
    try:
        # Extracting requirements params
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # Checking requirements params
        required_params = ['server', 'port']
        return all(param in query_params for param in required_params)
        
    except Exception:
        return False

@lru_cache(maxsize=128)
def extract_proxies_cached(message) -> List[str]:
    return extract_proxies_from_message(message)
    
async def fetch_configs_and_proxies(client, channel):
    channel_configs = {"vless": [], "vmess": [], "shadowsocks": [], "trojan": []}
    channel_proxies = []
    try:
        await client.get_entity(channel)
    except ChannelInvalidError as e:
        logger.error(f"Channel {channel} does not exist or is inaccessible: {str(e)}")
        return channel_configs, channel_proxies, False

    try:
        message_count = 0
        today = datetime.now().date()
        last_day = today - timedelta(days=1)

        async for message in client.iter_messages(channel, limit=200):
            message_count += 1
            if message.date:
                message_date = message.date.date()
                if message_date not in [today] and message_date < last_day:
                    continue
                if isinstance(message, Message) and message.message:
                    text = message.message
                    # Extracting configs 
                    for protocol, config_pattern in CONFIG_PATTERNS.items():
                        matches = re.findall(config_pattern, text)
                        if matches:
                            logger.info(f"Found {len(matches)} {protocol} configs in message from {channel}")
                            channel_configs[protocol].extend(matches)
                    # Extracting proxies
                    if message_date >= last_day:
                        proxy_links = extract_proxies_cached(message)
                        if proxy_links:
                            logger.info(f"Found {len(proxy_links)} proxies in message from {channel}")
                            channel_proxies.extend(proxy_links)
            else:
                continue

        logger.info(f"Processed {message_count} messages from {channel}, found {sum(len(configs) for configs in channel_configs.values())} configs, {len(channel_proxies)} proxies")
        return channel_configs, channel_proxies, True
    except Exception as e:
        logger.error(f"Failed to fetch from {channel}: {str(e)}")
        return channel_configs, channel_proxies, False

def save_configs(configs, protocol):
    output_file = rf"Configs/{protocol}.txt"
    logger.info(f"Saving configs to {output_file}")
    with open(output_file, "w", encoding="utf-8") as f:
        if configs:
            for config in configs:
                f.write(config + "\n")
            logger.info(f"Saved {len(configs)} {protocol} configs to {output_file}")
        else:
            f.write(f"No configs found for {protocol}\n")
            logger.info(f"No {protocol} configs found")

def save_channel_status(stats):
    logger.info(f"Saving channel status to {CHANNELS_LOG}")
    stats_list = [{"channel": channel, **data} for channel, data in stats.items()]
    with open(CHANNELS_LOG, "w", encoding="utf-8") as f:
        json.dump(stats_list, f, ensure_ascii=False, indent=4)
    logger.info(f"Saved channel status to {CHANNELS_LOG}")

def save_proxies(proxies):
    output_file = rf"Configs/proxies.txt"
    logger.info(f"Saving proxies to {output_file}")
    with open(output_file, "w", encoding="utf-8") as f:
        if proxies:
            for proxy in proxies:
                f.write(f"{proxy}\n")
            logger.info(f"Saved {len(proxies)} proxies to {output_file}")
        else:
            f.write("No proxies found.\n")
            logger.info("No proxies found")

def post_configs():
    pass

async def main():
    logger.info("Starting main function")
    
    TELEGRAM_CHANNELS = load_channels()
    session = StringSession(SESSION)
    CHANNELS_STATUS = {}
    ALL_CONFIGS = {"vless": [], "vmess": [], "shadowsocks": [], "trojan": []}
    ALL_PROXIES = []


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
                    channel_configs, channel_proxies, is_valid = await fetch_configs_and_proxies(client, channel)
                    if not is_valid:
                        CHANNELS_STATUS[channel] = {
                            "vless_count": 0,
                            "vmess_count": 0,
                            "shadowsocks_count": 0,
                            "trojan_count": 0,
                            "proxy_count": 0,
                            "total_configs": 0,
                            "error": "Channel does not exist or is inaccessible"
                        }
                        continue

                    total_configs = sum(len(configs) for configs in channel_configs.values())
                    proxy_count = len(channel_proxies)

                    CHANNELS_STATUS[channel] = {
                        "vless_count": len(channel_configs["vless"]),
                        "vmess_count": len(channel_configs["vmess"]),
                        "shadowsocks_count": len(channel_configs["shadowsocks"]),
                        "trojan_count": len(channel_configs["trojan"]),
                        "proxy_count": proxy_count,
                        "total_configs": total_configs,
                    }
                    for protocol in ALL_CONFIGS:
                        ALL_CONFIGS[protocol].extend(channel_configs[protocol])
                    ALL_PROXIES.extend(channel_proxies)
                except Exception as e:
                    CHANNELS_STATUS[channel] = {
                        "vless_count": 0,
                        "vmess_count": 0,
                        "shadowsocks_count": 0,
                        "trojan_count": 0,
                        "proxy_count": 0,
                        "total_configs": 0,
                        "score": 0,
                        "error": str(e)
                    }
                    logger.error(f"Channel {channel} is invalid: {str(e)}")

            for protocol in ALL_CONFIGS:
                save_configs(ALL_CONFIGS[protocol], protocol)
                save_proxies(ALL_PROXIES)
                save_channel_status(CHANNELS_STATUS)


    except Exception as e:
        logger.error(f"Error in main loop: {str(e)}")
        print(f"Error in main loop: {str(e)}")
        return

    logger.info("Config+proxy collection process completed")

if __name__ == "__main__":
    asyncio.run(main())