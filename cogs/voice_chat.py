import discord
from discord.ext import commands, voice_recv
import asyncio
import os

# Imports from your utils
from utils.neural import get_kenna_response, clear_user_memory
from utils.speech import generate_voice_file
from utils.ears import listen_to_mic, calibrate_mic      # LOCAL EARS
from utils.discord_ears import TranscribingSink, process_audio_streams # DISCORD EARS
import config

class VoiceChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_voice = config.DEFAULT_VOICE
        self.input_mode = 'discord'  # Options: 'discord' (Default) or 'local'
        
        # State trackers
        self.sink = None
        self.processing_task = None   # For Discord Ears
        self.local_loop_task = None   # For Local Ears

    # --- INPUT MODE SWITCHING ---
    @commands.command()
    async def ears(self, ctx, mode: str):
        """Switch between 'discord' (all users) and 'local' (host mic)."""
        mode = mode.lower()
        if mode not in ['discord', 'local']:
            return await ctx.send("Usage: `!ears discord` or `!ears local`")
        
        self.input_mode = mode
        await ctx.send(f"🔄 Switching ears to: **{mode.upper()}**...")

        # If currently connected, restart listening to apply change
        if ctx.voice_client:
            await self._stop_listening(ctx)
            await self._start_listening(ctx)

    async def _start_listening(self, ctx):
        """Starts the appropriate listening task based on input_mode."""
        vc = ctx.voice_client
        if not vc: return

        if self.input_mode == 'discord':
            await ctx.send("👂 Connected to Discord Audio (Listening to everyone).")
            self.sink = TranscribingSink(self.on_voice_transcript)
            vc.listen(self.sink)
            self.processing_task = self.bot.loop.create_task(process_audio_streams(self.sink, self.bot))
        
        elif self.input_mode == 'local':
            await ctx.send("🎤 Connected to Local Mic (Listening to HOST only).")
            # Calibrate once before starting loop
            await self.bot.loop.run_in_executor(None, calibrate_mic)
            self.local_loop_task = self.bot.loop.create_task(self.local_mic_loop(ctx, vc))

    async def _stop_listening(self, ctx):
        """Stops whatever listening task is currently running."""
        # Stop Discord Ears
        if ctx.voice_client and ctx.voice_client.is_listening():
            ctx.voice_client.stop_listening()
        if self.processing_task:
            self.processing_task.cancel()
            self.processing_task = None
        
        # Stop Local Ears
        if self.local_loop_task:
            self.local_loop_task.cancel()
            self.local_loop_task = None

    # --- LISTENING LOOPS ---
    
    # 1. DISCORD EARS CALLBACK
    async def on_voice_transcript(self, user_id, text):
        user = self.bot.get_user(user_id)
        name = user.display_name if user else "Unknown"
        print(f"👂 Heard {name}: {text}")
        await self.process_and_speak(user_id, text)

    # 2. LOCAL EARS LOOP
    async def local_mic_loop(self, ctx, vc):
        print("🎤 Local Mic Loop Started")
        while vc.is_connected() and self.input_mode == 'local':
            text = await self.bot.loop.run_in_executor(None, listen_to_mic)
            if text:
                print(f"🎤 Host Said: {text}")
                await self.process_and_speak(ctx.author.id, text)
            await asyncio.sleep(0.05)

    # --- RESPONSE LOGIC (SHARED) ---
    async def process_and_speak(self, user_id, text):
        """Shared function for handling input from ANY source."""
        
        # 1. Get the Name
        user = self.bot.get_user(user_id)
        # If intents are fixed, this will now be "jinx" or "jinx.sys"
        user_name = user.display_name if user else "Unknown"

        # 2. Check commands
        if "leave" in text.lower() and "kenna" in text.lower():
            if self.bot.voice_clients:
                await self.bot.voice_clients[0].disconnect()
            return

        # 3. Think (Pass user_name to brain now!)
        reply = await self.bot.loop.run_in_executor(
            None, get_kenna_response, user_id, user_name, text
        )
        print(f"Kenna: {reply}")

        # 3. Speak
        vc = self.bot.voice_clients[0] if self.bot.voice_clients else None
        if vc:
            audio_file = await self.bot.loop.run_in_executor(
                None, generate_voice_file, reply, self.current_voice, config.VOICE_SPEED
            )
            
            if vc.is_playing():
                vc.stop()
            
            def cleanup(e):
                if os.path.exists(audio_file): os.remove(audio_file)

            vc.play(discord.FFmpegPCMAudio(audio_file), after=cleanup)

    # --- COMMANDS ---
    @commands.command()
    async def join(self, ctx):
        if not ctx.author.voice:
            return await ctx.send("Join a VC first.")
        
        channel = ctx.author.voice.channel
        # IMPORTANT: Always connect with VoiceRecvClient to support discord ears
        await channel.connect(cls=voice_recv.VoiceRecvClient)
        await self._start_listening(ctx)

    @commands.command()
    async def leave(self, ctx):
        await self._stop_listening(ctx)
        if ctx.voice_client:
            await ctx.voice_client.disconnect()

    @commands.command()
    async def forget(self, ctx):
        cleared = clear_user_memory(ctx.author.id)
        await ctx.send(f"Memory wiped." if cleared else "I don't know you.")

    @commands.command()
    async def voice(self, ctx, new_voice: str):
        self.current_voice = new_voice.lower()
        await ctx.send(f"Voice set to `{self.current_voice}`.")

async def setup(bot):
    await bot.add_cog(VoiceChat(bot))