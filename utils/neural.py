import ollama
import re
from config import SYSTEM_PROMPT

# This dictionary stores history like: { user_id: [messages] }
user_memories = {}

def get_kenna_response(user_id, user_input):
    """Retrieves or creates a specific memory for each Discord user."""
    global user_memories
    
    # 1. If we've never talked to this user, give them a blank history
    if user_id not in user_memories:
        user_memories[user_id] = []
    
    # 2. Add the new message to THEIR specific history
    user_memories[user_id].append({'role': 'user', 'content': user_input})
    
    # 3. Keep only the last 10 messages for THIS user
    if len(user_memories[user_id]) > 10:
        user_memories[user_id] = user_memories[user_id][-10:]
    
    # 4. Combine system prompt with their personal history
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}] + user_memories[user_id]
    
    try:
        response = ollama.chat(model='dolphin-llama3', messages=messages)
        reply = response['message']['content'].strip()
        
        # 5. Save Kenna's reply to their history too
        user_memories[user_id].append({'role': 'assistant', 'content': reply})
        
        return re.sub(r'[*_~#]', '', reply)
    except Exception as e:
        print(f"🧠 Brain Error for user {user_id}: {e}")
        return "My brain is fried. Ask again."