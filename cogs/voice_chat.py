import discord
from discord.ext import commands
import asyncio
import os
from utils.neural import get_kenna_response, clear_user_memory
from utils.speech import generate_voice_file
from utils.ears import listen_to_mic, calibrate_mic # New import
import config

class VoiceChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_voice = config.DEFAULT_VOICE
        self.is_listening = False

    @commands.command()
    async def join(self, ctx):
        """Joins VC, calibrates mic once, and starts the loop."""
        if not ctx.author.voice:
            return await ctx.send("Join a voice channel first, loser.")

        channel = ctx.author.voice.channel
        vc = await channel.connect()
        self.is_listening = True
        
        await ctx.send(f"I'm in. Voice: `{self.current_voice}`. Calibrating mic (shhh)...")
        
        # 1. Calibrate ONCE at the start (runs in background so bot doesn't freeze)
        await self.bot.loop.run_in_executor(None, calibrate_mic)
        await ctx.send("🎤 Calibration done. Start talking.")

        # --- The Listening Loop ---
        while vc.is_connected() and self.is_listening:
            # 2. Listen (Non-blocking)
            user_speech = await self.bot.loop.run_in_executor(None, listen_to_mic)

            if user_speech:
                print(f"You ({ctx.author.name}) said: {user_speech}")
                
                if any(word in user_speech.lower() for word in ['quit', 'exit', 'stop']):
                    self.is_listening = False
                    await ctx.send("Bye.")
                    await vc.disconnect()
                    break

                # Show 'Typing' status so you know she heard you
                async with ctx.typing():
                    # 3. Think (Non-blocking - fixes the freeze!)
                    reply = await self.bot.loop.run_in_executor(
                        None, get_kenna_response, ctx.author.id, user_speech
                    )

                    print(f"Kenna: {reply}")
                    
                    # 4. Generate Audio (Non-blocking)
                    audio_file = await self.bot.loop.run_in_executor(
                        None, generate_voice_file, reply, self.current_voice, config.VOICE_SPEED
                    )

                # 5. Play Audio
                if vc.is_playing():
                    vc.stop()
                
                # Define a callback to delete the file after it finishes playing
                def after_playing(error):
                    if audio_file and os.path.exists(audio_file):
                        os.remove(audio_file)

                vc.play(discord.FFmpegPCMAudio(audio_file), after=after_playing)

            await asyncio.sleep(0.05) # Slightly faster loop

    @commands.command()
    async def forget(self, ctx):
        """Wipes Kenna's memory of YOU."""
        cleared = clear_user_memory(ctx.author.id)
        if cleared:
            await ctx.send(f"Who are you again? (Memory wiped for {ctx.author.name})")
        else:
            await ctx.send("I already don't know who you are.")

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