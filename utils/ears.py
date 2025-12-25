import speech_recognition as sr

recognizer = sr.Recognizer()

def calibrate_mic():
    """Adjusts for noise ONCE and then LOCKS the sensitivity."""
    with sr.Microphone() as source:
        print("🎤 Calibrating background noise... (Please be quiet)")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        # PRO MOVE: Lock the sensitivity so she doesn't go deaf if you shout
        # slightly increase the threshold to ignore breathing/keyboard clicks
        recognizer.energy_threshold += 50  
        recognizer.dynamic_energy_threshold = False 
        
        print(f"✅ Calibration complete. Sensitivity locked at {recognizer.energy_threshold}")

def listen_to_mic():
    """Listens for a phrase using the locked settings."""
    with sr.Microphone() as source:
        try:
            # timeout=5 means if you say nothing for 5s, she stops waiting
            # phrase_time_limit=10 means she cuts you off if you ramble for 10s
            audio = recognizer.listen(source, timeout=2.5, phrase_time_limit=10)
            return recognizer.recognize_google(audio)
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"👂 Ear Error: {e}")
            return None