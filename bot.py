import os
import re
import asyncio
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from github import Github
from dotenv import load_dotenv

class ConfigCollector:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Telegram settings
        self.telegram_api_id = os.getenv('TELEGRAM_API_ID')
        self.telegram_api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone_number = os.getenv('TELEGRAM_PHONE')
        self.target_channel = os.getenv('TARGET_CHANNEL')
        
        # GitHub settings
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_repo_name = os.getenv('GITHUB_REPOSITORY')
        
        # Config patterns
        self.patterns = {
            'vless': re.compile(r'vless://[^\s]+'),
            'vmess': re.compile(r'vmess://[^\s]+'),
            'ss': re.compile(r'ss://[^\s]+'),
            'mtproto': re.compile(r'https://t\.me/proxy\?[^\s]+')
        }
        
        # Storage for collected configs
        self.configs = {k: set() for k in self.patterns.keys()}
        
        # Load channels list
        self.channels = self._load_channels()
        
        # Initialize Telegram client
        self.client = TelegramClient('session_name', self.telegram_api_id, self.telegram_api_hash)

    def _load_channels(self):
        """Load channels from channels.txt file"""
        try:
            with open('channels.txt', 'r') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except FileNotFoundError:
            print("channels.txt file not found!")
            return []

    async def _collect_configs_from_message(self, message):
        """Extract configs from a single message"""
        found = {k: set() for k in self.patterns.keys()}
        if not message.text:
            return found
            
        for config_type, pattern in self.patterns.items():
            matches = pattern.findall(message.text)
            if matches:
                found[config_type].update(matches)
                
        return found

    async def _process_channel(self, channel):
        """Process a channel to collect configs"""
        try:
            print(f"Scanning channel: {channel}")
            async for message in self.client.iter_messages(channel, limit=200):
                found = await self._collect_configs_from_message(message)
                for config_type, configs in found.items():
                    if configs:
                        self.configs[config_type].update(configs)
        except Exception as e:
            print(f"Error processing channel {channel}: {str(e)}")

    async def _send_to_telegram(self, configs_dict):
        """Send configs to target channel"""
        try:
            entity = await self.client.get_entity(self.target_channel)
            
            for config_type, configs in configs_dict.items():
                if configs:
                    msg = f"🆕 {config_type.upper()} Configs ({len(configs)}):\n\n" + "\n".join(list(configs)[:50])
                    await self.client.send_message(entity, msg)
                    print(f"Sent {len(configs)} {config_type} configs to channel")
        except Exception as e:
            print(f"Error sending to channel: {str(e)}")

    def _update_github(self, configs_dict):
        """Update GitHub repository with new configs"""
        if not self.github_token or not self.github_repo_name:
            print("GitHub settings missing!")
            return
            
        try:
            g = Github(self.github_token)
            repo = g.get_repo(self.github_repo_name)
            
            for config_type, configs in configs_dict.items():
                if configs:
                    path = f"configs/{config_type}.txt"
                    content = "\n".join(configs)
                    
                    try:
                        file = repo.get_contents(path)
                        repo.update_file(path, f"Update {config_type} configs", content, file.sha)
                    except:
                        repo.create_file(path, f"Add {config_type} configs", content)
                        
                    print(f"Updated {len(configs)} {config_type} configs on GitHub")
        except Exception as e:
            print(f"Error updating GitHub: {str(e)}")

    async def login(self):
        """Login to Telegram account"""
        await self.client.connect()
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone_number)
            code = input("Enter received code: ")
            try:
                await self.client.sign_in(self.phone_number, code)
            except SessionPasswordNeededError:
                password = input("Enter 2FA password: ")
                await self.client.sign_in(password=password)

    async def collect_and_process(self):
        """Main collection and processing function"""
        print("Starting config collection process...")
        
        # Clear previous configs
        for k in self.configs:
            self.configs[k].clear()
        
        # Process channels
        for channel in self.channels:
            await self._process_channel(channel)
            
        # Filter empty configs
        collected = {k: v for k, v in self.configs.items() if v}
        
        if collected:
            # Send to Telegram
            await self._send_to_telegram(collected)
            
            # Update GitHub
            self._update_github(collected)
            
            print("Process completed successfully!")
            return True
        else:
            print("No new configs found!")
            return False

    async def run(self, interval=None):
        """Main run method"""
        try:
            await self.login()
            
            while True:
                success = await self.collect_and_process()
                if interval is None:
                    break
                    
                print(f"Waiting for {interval} seconds...")
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            print("Stopping bot...")
        finally:
            await self.client.disconnect()


if __name__ == "__main__":
    bot = ConfigCollector()
    
    # Run once
    asyncio.run(bot.collect_and_process())
    
    # Run periodically (every 1 hour)
    # asyncio.run(bot.run(interval=3600))