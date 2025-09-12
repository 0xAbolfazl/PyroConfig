import logging
import os
import json
import asyncio
from telethon.sessions import StringSession
from telethon.sync import TelegramClient
from telethon.tl.types import Message, MessageEntityTextUrl, MessageEntityUrl
from telethon.errors import ChannelInvalidError
from datetime import timedelta, datetime
import re
from typing import List, Dict, Tuple
from urllib.parse import urlparse, parse_qs
import random


class TelegramConfigCollector:
    """A class to collect and manage proxy configurations from Telegram channels."""
    
    def __init__(self):
        """Initialize the Telegram config collector with environment variables and settings."""
        self.SESSION = os.getenv('SESSION_STRING')
        self.API_ID = int(os.getenv('API_ID'))
        self.API_HASH = os.getenv('API_HASH')
        self.CHANNELS_FILE = 'channels.json'
        self.LOGS_FILE = 'Logs/logs.txt'
        self.CONFIG_FOLDER = 'Configs'
        self.LOGS_FOLDER = 'Logs'
        self.CHANNELS_LOG = 'Logs/channels_log.json'
        self.CONFIG_CHANNEL = os.getenv('CHANNEL_ID')
        
        # Configuration patterns for different proxy types
        self.CONFIG_PATTERNS = {
            "vless": r"vless://[^\s]+",
            "vmess": r"vmess://[^\s]+",
            "shadowsocks": r"ss://[^\s]+",
            "trojan": r"trojan://[^\s]+"
        }
        
        # Pattern to detect Telegram proxy URLs
        self.PROXY_PATTERN = r'https?://t\.me/proxy\?[^\s]+'
        
        # Initialize folders and logging
        self._setup_folders()
        self._setup_logging()
        
        # Data storage
        self.all_configs = {"vless": [], "vmess": [], "shadowsocks": [], "trojan": []}
        self.all_proxies = []
        self.channels_status = {}
    
    def _setup_folders(self):
        """Create necessary folders if they don't exist."""
        if not os.path.exists(self.CONFIG_FOLDER):
            os.makedirs(self.CONFIG_FOLDER)
        
        if not os.path.exists(self.LOGS_FOLDER):
            os.makedirs(self.LOGS_FOLDER)
    
    def _setup_logging(self):
        """Configure logging settings."""
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Add file handler
        file_handler = logging.FileHandler(
            self.LOGS_FILE, mode='w', encoding='utf-8'
        )
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        self.logger.addHandler(file_handler)
    
    def load_channels(self) -> List[str]:
        """
        Load channel list from JSON file.
        
        Returns:
            List of channel usernames/IDs
        """
        try:
            with open(self.CHANNELS_FILE, 'r') as ch:
                channels_list = json.load(ch)['all_channels']
                self.logger.info(f'{len(channels_list)} Channels Loaded!')
                return channels_list
        except FileNotFoundError:
            self.logger.error(f"Channels file {self.CHANNELS_FILE} not found!")
            return []
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in {self.CHANNELS_FILE}!")
            return []
        except KeyError:
            self.logger.error(f"Missing 'all_channels' key in {self.CHANNELS_FILE}!")
            return []
    
    def is_valid_proxy_url(self, url: str) -> bool:
        """
        Validate if a URL is a proper Telegram proxy URL.
        
        Args:
            url: The URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        if not url.startswith("https://t.me/proxy?"):
            return False
        
        try:
            # Extract and check required parameters
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            
            # Check for required parameters
            required_params = ['server', 'port']
            return all(param in query_params for param in required_params)
        except Exception:
            return False
    
    def extract_proxies_from_message(self, message: Message) -> List[str]:
        """
        Extract proxy URLs from a Telegram message.
        
        Args:
            message: Telegram message object
            
        Returns:
            List of proxy URLs found in the message
        """
        proxies = []
        
        if not hasattr(message, 'message') or not message.message:
            return proxies
        
        text = message.message    
        
        # Find proxies in text using regex
        text_proxies = re.findall(self.PROXY_PATTERN, text)
        proxies.extend(text_proxies)
        
        # Extract proxies from message entities
        if hasattr(message, 'entities') and message.entities:
            for entity in message.entities:
                try:
                    if isinstance(entity, (MessageEntityTextUrl, MessageEntityUrl)):
                        # Extract URL from entity
                        if hasattr(entity, 'url') and entity.url:
                            url = entity.url
                        else:
                            offset = entity.offset
                            length = entity.length
                            if offset + length <= len(text):
                                url = text[offset:offset+length]
                            else:
                                continue
                        
                        # Validate the proxy URL
                        if self.is_valid_proxy_url(url):
                            proxies.append(url)
                except (IndexError, AttributeError) as e:
                    continue
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(proxies))
    
    async def fetch_configs_and_proxies(self, client: TelegramClient, channel: str) -> Tuple[Dict[str, List[str]], List[str], bool]:
        """
        Fetch configurations and proxies from a Telegram channel.
        
        Args:
            client: Authenticated Telegram client
            channel: Channel username/ID to fetch from
            
        Returns:
            Tuple of (configs_dict, proxies_list, success_status)
        """
        channel_configs = {"vless": [], "vmess": [], "shadowsocks": [], "trojan": []}
        channel_proxies = []
        
        # Verify channel accessibility
        try:
            await client.get_entity(channel)
        except ChannelInvalidError as e:
            self.logger.error(f"Channel {channel} does not exist or is inaccessible: {str(e)}")
            return channel_configs, channel_proxies, False
        
        try:
            message_count = 0
            today = datetime.now().date()
            last_day = today - timedelta(days=1)
            
            # Iterate through recent messages
            async for message in client.iter_messages(channel, limit=200):
                message_count += 1
                
                if not (message and hasattr(message, 'date') and message.date):
                    continue
                
                message_date = message.date.date()
                
                # Skip messages older than yesterday
                if message_date not in [today] and message_date < last_day:
                    continue
                
                if isinstance(message, Message) and message.message:
                    text = message.message
                    
                    # Extract configurations for each protocol
                    for protocol, config_pattern in self.CONFIG_PATTERNS.items():
                        matches = re.findall(config_pattern, text)
                        if matches:
                            self.logger.info(f"Found {len(matches)} {protocol} configs in message from {channel}")
                            channel_configs[protocol].extend(matches)
                    
                    # Extract proxies from recent messages
                    if message_date >= last_day:
                        proxy_links = self.extract_proxies_from_message(message)
                        if proxy_links:
                            self.logger.info(f"Found {len(proxy_links)} proxies in message from {channel}")
                            channel_proxies.extend(proxy_links)
            
            self.logger.info(
                f"Processed {message_count} messages from {channel}, "
                f"found {sum(len(configs) for configs in channel_configs.values())} configs, "
                f"{len(channel_proxies)} proxies"
            )
            return channel_configs, channel_proxies, True
        
        except Exception as e:
            self.logger.error(f"Failed to fetch from {channel}: {str(e)}")
            return channel_configs, channel_proxies, False
    
    def format_proxies_in_rows(self, proxies: List[str], per_row: int = 4) -> str:
        """
        Format proxy URLs into markdown rows.
        
        Args:
            proxies: List of proxy URLs
            per_row: Number of proxies per row
            
        Returns:
            Formatted string with proxies in rows
        """
        lines = []
        for i in range(0, len(proxies), per_row):
            chunk = proxies[i:i+per_row]
            line = " | ".join([f"[Proxy {i+j+1}]({proxy})" for j, proxy in enumerate(chunk)])
            lines.append(line)
        return "\n".join(lines)
    
    def save_configs(self, configs: List[str], protocol: str):
        """
        Save configurations to a file.
        
        Args:
            configs: List of configuration strings
            protocol: Protocol name (vless, vmess, etc.)
        """
        output_file = os.path.join(self.CONFIG_FOLDER, f"{protocol}.txt")
        self.logger.info(f"Saving configs to {output_file}")
        
        with open(output_file, "w", encoding="utf-8") as f:
            if configs:
                for config in configs:
                    f.write(config + "\n")
                self.logger.info(f"Saved {len(configs)} {protocol} configs to {output_file}")
            else:
                f.write(f"No configs found for {protocol}\n")
                self.logger.info(f"No {protocol} configs found")
    
    def save_proxies(self, proxies: List[str]):
        """Save proxy URLs to a file."""
        output_file = os.path.join(self.CONFIG_FOLDER, "proxies.txt")
        self.logger.info(f"Saving proxies to {output_file}")
        
        with open(output_file, "w", encoding="utf-8") as f:
            if proxies:
                for proxy in proxies:
                    f.write(f"{proxy}\n")
                self.logger.info(f"Saved {len(proxies)} proxies to {output_file}")
            else:
                f.write("No proxies found.\n")
                self.logger.info("No proxies found")
    
    def save_channel_status(self):
        """Save channel status information to a JSON file."""
        self.logger.info(f"Saving channel status to {self.CHANNELS_LOG}")
        
        stats_list = [
            {"channel": channel, **data} 
            for channel, data in self.channels_status.items()
        ]
        
        with open(self.CHANNELS_LOG, "w", encoding="utf-8") as f:
            json.dump(stats_list, f, ensure_ascii=False, indent=4)
        
        self.logger.info(f"Saved channel status to {self.CHANNELS_LOG}")
    
    async def post_data_to_channel(self, client: TelegramClient):
        """
        Post collected data to the configured channel.
        
        Args:
            client: Authenticated Telegram client
        """
        if not self.channels_status:
            self.logger.warning("No channel stats available to determine the best channel.")
            return
        
        # Find the channel with the highest score
        best_channel = None
        best_score = -1
        
        for channel, stats in self.channels_status.items():
            score = stats.get("score", 0)
            if score > best_score:
                best_score = score
                best_channel = channel
        
        if not best_channel or best_score == 0:
            self.logger.warning("No valid channel with configs found to post.")
            return
        
        # Fetch fresh configs and proxies from the best channel
        channel_configs = {"vless": [], "vmess": [], "shadowsocks": [], "trojan": []}
        channel_proxies = []
        
        try:
            temp_configs, temp_proxies, _ = await self.fetch_configs_and_proxies(client, best_channel)
            for protocol in channel_configs:
                channel_configs[protocol].extend(temp_configs[protocol])
            channel_proxies.extend(temp_proxies)
        except Exception as e:
            self.logger.error(f"Failed to fetch configs/proxies from best channel {best_channel}: {str(e)}")
            return
        
        # Prepare all configs for posting
        all_channel_configs = []
        for protocol in channel_configs:
            all_channel_configs.extend(channel_configs[protocol])
        
        if not all_channel_configs:
            self.logger.warning(f"No configs found from the best channel {best_channel} to post.")
            return
        
        # Create message with random configs
        message = f"Configs for V2RAY\n\n```"
        
        # Select 5 random configs
        for _ in range(min(5, len(all_channel_configs))):
            selected_config = random.choice(all_channel_configs)
            message += f'{selected_config}\n'
        
        message += '```'
        
        # Add proxies if available
        if self.all_proxies:
            random.shuffle(self.all_proxies)
            fresh_proxies = self.all_proxies[:8] if len(self.all_proxies) >= 8 else self.all_proxies
            proxies_formatted = self.format_proxies_in_rows(fresh_proxies, per_row=4)
            message += "\n" + proxies_formatted
        
        # Add channel reference
        message += f"\n\n🆔 {self.CONFIG_CHANNEL}"
        
        # Send message
        try:
            await client.send_message(self.CONFIG_CHANNEL, message, parse_mode="markdown")
            self.logger.info(f"Posted configs + proxies from {best_channel} to {self.CONFIG_CHANNEL}")
        except Exception as e:
            self.logger.error(f"Failed to post config/proxies to {self.CONFIG_CHANNEL}: {str(e)}")
    
    async def run(self):
        """Main execution method for the config collector."""
        self.logger.info("Starting Telegram Config Collector")
        
        # Load channels and initialize Telegram client
        telegram_channels = self.load_channels()
        
        if not telegram_channels:
            self.logger.error("No channels to process. Exiting.")
            return
        
        session = StringSession(self.SESSION)
        
        try:
            async with TelegramClient(session, self.API_ID, self.API_HASH) as client:
                # Check if session is authorized
                if not await client.is_user_authorized():
                    self.logger.error("Invalid session. Please check your SESSION_STRING.")
                    return
                
                # Process each channel
                for channel in telegram_channels:
                    self.logger.info(f"Fetching configs/proxies from {channel}...")
                    
                    try:
                        channel_configs, channel_proxies, is_valid = await self.fetch_configs_and_proxies(client, channel)
                        
                        if not is_valid:
                            self.channels_status[channel] = {
                                "vless_count": 0,
                                "vmess_count": 0,
                                "shadowsocks_count": 0,
                                "trojan_count": 0,
                                "proxy_count": 0,
                                "total_configs": 0,
                                "score": 0,
                                "error": "Channel does not exist or is inaccessible"
                            }
                            continue
                        
                        # Calculate statistics
                        total_configs = sum(len(configs) for configs in channel_configs.values())
                        proxy_count = len(channel_proxies)
                        score = total_configs + proxy_count
                        
                        # Update channel status
                        self.channels_status[channel] = {
                            "vless_count": len(channel_configs["vless"]),
                            "vmess_count": len(channel_configs["vmess"]),
                            "shadowsocks_count": len(channel_configs["shadowsocks"]),
                            "trojan_count": len(channel_configs["trojan"]),
                            "proxy_count": proxy_count,
                            "total_configs": total_configs,
                            "score": score
                        }
                        
                        # Aggregate all configs and proxies
                        for protocol in self.all_configs:
                            self.all_configs[protocol].extend(channel_configs[protocol])
                            self.logger.info(f"Found {len(self.all_configs[protocol])} {protocol} configs")
                        
                        self.all_proxies.extend(channel_proxies)
                        
                    except Exception as e:
                        self.channels_status[channel] = {
                            "vless_count": 0,
                            "vmess_count": 0,
                            "shadowsocks_count": 0,
                            "trojan_count": 0,
                            "proxy_count": 0,
                            "total_configs": 0,
                            "score": 0,
                            "error": str(e)
                        }
                        self.logger.error(f"Channel {channel} is invalid: {str(e)}")
                
                # Save results
                for protocol in self.all_configs:
                    self.save_configs(self.all_configs[protocol], protocol)
                
                self.save_proxies(self.all_proxies)
                self.save_channel_status()
                
                # Post to channel
                await self.post_data_to_channel(client)
                
        except Exception as e:
            self.logger.error(f"Error in main loop: {str(e)}")
            return
        
        self.logger.info("Config+proxy collection process completed successfully")


async def main():
    """Main function to run the Telegram Config Collector."""
    collector = TelegramConfigCollector()
    await collector.run()


if __name__ == "__main__":
    asyncio.run(main())