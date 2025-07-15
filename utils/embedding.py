import openai
import os

def get_embedding(text: str) -> list:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError('OPENAI_API_KEY not set')
    response = openai.Embedding.create(
        input=text,
        model='text-embedding-ada-002',
        api_key=api_key
    )
    return response['data'][0]['embedding'] 