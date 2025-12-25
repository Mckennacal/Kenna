import ollama
import re
from config import SYSTEM_PROMPT

def get_kenna_response(user_input):
    """Calls Ollama and cleans the response."""
    response = ollama.chat(model='dolphin-llama3', messages=[
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': user_input}
    ])
    
    reply = response['message']['content'].strip()
    return re.sub(r'[*_~#]', '', reply) # Remove markdown/asterisks