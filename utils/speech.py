import soundfile as sf
from kokoro import KPipeline
import uuid
import os

# Initialize pipeline once
pipeline = KPipeline(lang_code='a')

def generate_voice_file(text, voice_id, speed=1.1):
    """Turns text into audio and returns a unique filename."""
    
    # Generate a random filename so we don't overwrite files currently playing
    filename = f"reply_{uuid.uuid4().hex}.wav"
    
    generator = pipeline(text, voice=voice_id, speed=speed)
    for i, (gs, ps, audio) in enumerate(generator):
        sf.write(filename, audio, 24000)
        break # Return after first segment for speed
        
    return filename