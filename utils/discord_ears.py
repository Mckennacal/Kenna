import discord
from discord.ext import voice_recv
import speech_recognition as sr
import wave
import time
import io
import asyncio

class TranscribingSink(voice_recv.AudioSink):
    def __init__(self, callback_func):
        super().__init__()
        self.callback_func = callback_func
        self.user_buffers = {} 
        self.last_speaking_time = {} 

    def wants_opus(self):
        return False # We want raw PCM

    def write(self, user, data):
        if user is None: return
        
        user_id = user.id
        if user_id not in self.user_buffers:
            self.user_buffers[user_id] = bytearray()
            self.last_speaking_time[user_id] = time.time()

        self.user_buffers[user_id].extend(data.pcm)
        self.last_speaking_time[user_id] = time.time()

    def cleanup(self):
        self.user_buffers.clear()

async def process_audio_streams(sink, bot):
    """Background task to check for silence and transcribe."""
    recognizer = sr.Recognizer()
    
    while True:
        current_time = time.time()
        users_to_process = []

        # Check for silence (> 0.6s) to determine end of sentence
        for user_id, last_time in list(sink.last_speaking_time.items()):
            if current_time - last_time > 0.6: 
                # Only process if they actually said something substantial
                if user_id in sink.user_buffers and len(sink.user_buffers[user_id]) > 30000:
                    users_to_process.append(user_id)
        
        for user_id in users_to_process:
            audio_data = sink.user_buffers.pop(user_id)
            del sink.last_speaking_time[user_id]

            # Convert raw audio to WAV container for Google Speech Recognition
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(2) 
                wav_file.setsampwidth(2) 
                wav_file.setframerate(48000) 
                wav_file.writeframes(audio_data)
            
            wav_buffer.seek(0)

            try:
                # Transcribe in a separate thread
                with sr.AudioFile(wav_buffer) as source:
                    audio_content = recognizer.record(source)
                    text = await bot.loop.run_in_executor(
                        None, lambda: recognizer.recognize_google(audio_content)
                    )
                    
                    if text:
                        await sink.callback_func(user_id, text)

            except Exception:
                pass # Usually just noise

        await asyncio.sleep(0.1)