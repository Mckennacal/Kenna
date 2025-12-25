import discord
from discord.ext import commands
import asyncio
from utils.neural import get_kenna_response
from utils.speech import generate_voice_file
import config

class VoiceChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_voice = config.DEFAULT_VOICE
        self.is_listening = False

    @commands.command()
    async def join(self, ctx):
        """Joins VC and starts the local mic listening loop."""
        if not ctx.author.voice:
            return await ctx.send("Join a voice channel first, loser.")

        channel = ctx.author.voice.channel
        vc = await channel.connect()
        self.is_listening = True
        await ctx.send(f"I'm in. Voice: `{self.current_voice}`. Talk to your mic.")

        # --- The Listening Loop ---
        # We run this in the background so it doesn't freeze the bot
        while vc.is_connected() and self.is_listening:
            # We import the mic listener here to keep the cog clean
            from kenna import listen_to_mic 
            user_speech = await self.bot.loop.run_in_executor(None, listen_to_mic)

            if user_speech:
                print(f"You said: {user_speech}")
                
                # Check for exit commands
                if any(word in user_speech.lower() for word in ['quit', 'exit', 'stop']):
                    self.is_listening = False
                    await vc.disconnect()
                    break

                # 1. Get Brain Response from utils/neural.py
                reply = get_kenna_response(user_speech)
                
                # 2. Generate Voice from utils/speech.py
                audio_file = generate_voice_file(reply, self.current_voice, config.VOICE_SPEED)

                # 3. Play in Discord
                if vc.is_playing():
                    vc.stop()
                
                vc.play(discord.FFmpegPCMAudio(audio_file))

            await asyncio.sleep(0.1)

    @commands.command()
    async def voice(self, ctx, new_voice: str):
        """Changes Kenna's voice instantly."""
        self.current_voice = new_voice.lower()
        await ctx.send(f"Fine. Voice is now `{self.current_voice}`.")

    @commands.command()
    async def leave(self, ctx):
        """Kicks Kenna out of the VC."""
        self.is_listening = False
        if ctx.voice_client:
            await ctx.voice_client.disconnect()

async def setup(bot):
    await bot.add_cog(VoiceChat(bot))