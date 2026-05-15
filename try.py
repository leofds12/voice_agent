import anthropic
from backend.config import ANTHROPIC_API_KEY
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
response = client.messages.create(
    model='claude-3-haiku-20240307',
    max_tokens=100,
    messages=[{'role': 'user', 'content': 'Decí hola'}]
)
print(response.content[0].text)
