import discord
from discord.ext import commands
import asyncio
import speech_recognition as sr  # Added this import
from config import TOKEN, COMMAND_PREFIX

# 1. Initialize the recognizer here so it's accessible
recognizer = sr.Recognizer()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# 2. Add this function back so the Cog can use it
def listen_to_mic():
    """Listens to your local desk microphone."""
    with sr.Microphone() as source:
        print("\n🎤 Listening to YOU...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            return recognizer.recognize_google(audio)
        except:
            return None

async def load_extensions():
    await bot.load_extension('cogs.voice_chat')
    print("✅ Voice Chat Cog Loaded")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())