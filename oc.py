from openai import OpenAI
import sys
import os
import platform
from datetime import datetime
import json

from dotenv import load_dotenv

load_dotenv()

user_message = sys.argv[1] if len(sys.argv) > 1 else sys.exit("Usage: python oc.py 'your message here'")

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    sys.exit("Error: OPENAI_API_KEY is not set. Set it in your .env file.")

client = OpenAI(
    base_url="https://chat.oracle.com/api"
)

# Gather environment information
env_info = {
    "Operating System": f"{platform.system()} {platform.release()} ({platform.version()})",
    "Python Version": platform.python_version(),
    "Current Working Directory": os.getcwd(),
    "Shell": os.environ.get('SHELL', 'N/A'),
    "Current Date/Time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}
system_message = f'''
Use [environment_details] to tailor command-line or system-level responses.
<environment_details>
{json.dumps(env_info, indent=2)}
</environment_details>
'''

messages = [
    {"role": "system", "content": system_message},
    {"role": "user", "content": user_message}
]

completion = client.chat.completions.create(
    model="genai.openai.gpt-4.1",
    messages=messages,
    stream=True,
)

for chunk in completion:
    if hasattr(chunk, 'choices') and chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='')
print(end='\n\n')
