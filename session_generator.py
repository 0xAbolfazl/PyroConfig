from pip import main
main(['install', 'nest_asyncio'])

import os
import nest_asyncio
nest_asyncio.apply()

from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio

async def create_session():
    API_ID = os.getenv('API_ID')
    API_HASH = os.getenv('API_HASH')
    
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        session_string = client.session.save()
        print("✅ Session created successfully!")
        print(f"Session string: {session_string}")
        return session_string

session_str = asyncio.run(create_session())