import sys
sys.path.insert(0, 'functions/vendor')

import discord
from discord.ext import tasks
import json
import asyncio

import os

def handler(event, context):
    intents = discord.Intents.default()

    client = DiscordClient(event, intents=intents)
    asyncio.run(client.start(os.getenv("DISCORD_TOKEN")))

    print(event)
    return { 
        'message' : "success"
    }

class DiscordClient(discord.Client):
    def __init__(self, event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event
        self.channel_id = int(os.getenv("CHANNEL_ID"))
        self.group_id = int(os.getenv("ROLE_ID"))

    def build_message(self):
        error_str = json.dumps(self.event, indent=4, sort_keys=True)
        
        msg = f"<@&{self.group_id}> - Aucbot error triggered:\n```"
        msg += error_str
        msg += "```"

        return msg

    async def setup_hook(self) -> None:
        self.alert_error.start()

    async def on_ready(self):
        print(f'Logged in as {self.user}')

    @tasks.loop(seconds=10)
    async def alert_error(self):
        await self.wait_until_ready()
        channel = self.get_channel(self.channel_id)
        if not self.is_closed():
            msg = self.build_message()
            print("Sending message: ", msg)
            await channel.send(msg)
            await self.close()
