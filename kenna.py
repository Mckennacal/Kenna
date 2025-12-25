import discord
from discord.ext import commands
import asyncio
from config import TOKEN, COMMAND_PREFIX

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

async def load_extensions():
    await bot.load_extension('cogs.voice_chat')
    print("✅ Voice Chat Cog Loaded")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())