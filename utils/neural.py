import ollama
import re
import json
import os
from config import SYSTEM_PROMPT

# File where we store the chat logs
MEMORY_FILE = "memory.json"

# Dictionary to hold separate histories for each Discord user
user_memories = {}

def load_memory():
    """Loads saved conversations from the file on startup."""
    global user_memories
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                user_memories = json.load(f)
            print("🧠 Memory loaded successfully.")
        except Exception as e:
            print(f"⚠️ Brain damage (Could not load memory): {e}")
            user_memories = {}

def save_memory():
    """Writes the current memory to the file."""
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(user_memories, f, indent=4)
    except Exception as e:
        print(f"⚠️ Failed to save memory: {e}")

# Load memory immediately when the bot starts
load_memory()

def get_kenna_response(user_id, user_input):
    """Calls Ollama with memory of the last 10 messages for a specific user."""
    global user_memories
    
    # Convert ID to string because JSON only allows string keys
    user_id = str(user_id)
    
    # 1. Initialize history for new users
    if user_id not in user_memories:
        user_memories[user_id] = []
    
    # 2. Add the USER'S new message to their history
    user_memories[user_id].append({'role': 'user', 'content': user_input})
    
    # 3. Trim memory (Keep only last 10 messages to save RAM)
    if len(user_memories[user_id]) > 10:
        user_memories[user_id] = user_memories[user_id][-10:]
    
    # 4. Combine system prompt + their history
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}] + user_memories[user_id]
    
    try:
        response = ollama.chat(model='dolphin-llama3', messages=messages)
        reply = response['message']['content'].strip()
        
        # 5. Add KENNA'S reply to the history
        user_memories[user_id].append({'role': 'assistant', 'content': reply})
        
        # 6. SAVE PERMANENTLY
        save_memory()
        
        return re.sub(r'[*_~#]', '', reply)
    except Exception as e:
        print(f"🧠 Brain Error for user {user_id}: {e}")
        return "My brain is fried. Ask again."

def clear_user_memory(user_id):
    """Wipes the memory for a specific user."""
    user_id = str(user_id)
    if user_id in user_memories:
        del user_memories[user_id]
        save_memory() # Save the deletion
        return True
    return False