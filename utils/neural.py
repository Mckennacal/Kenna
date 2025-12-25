import ollama
import re
from config import SYSTEM_PROMPT

# Dictionary to hold separate histories for each Discord user
# Format: { user_id: [message_list] }
user_memories = {}

def get_kenna_response(user_id, user_input):
    """Calls Ollama with memory of the last 10 messages for a specific user."""
    global user_memories
    
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
        
        return re.sub(r'[*_~#]', '', reply)
    except Exception as e:
        print(f"🧠 Brain Error for user {user_id}: {e}")
        return "My brain is fried. Ask again."

def clear_user_memory(user_id):
    """Wipes the memory for a specific user."""
    if user_id in user_memories:
        del user_memories[user_id]
        return True
    return False