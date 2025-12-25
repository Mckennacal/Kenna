import soundfile as sf
from kokoro import KPipeline

pipeline = KPipeline(lang_code='a')

def generate_voice_file(text, voice_id, speed=1.1):
    """Turns text into audio and saves it as reply.wav."""
    generator = pipeline(text, voice=voice_id, speed=speed)
    for i, (gs, ps, audio) in enumerate(generator):
        sf.write("reply.wav", audio, 24000)
        break # Return after first segment for speed
    return "reply.wav"