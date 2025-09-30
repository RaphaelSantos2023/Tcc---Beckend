from google import genai
import os

cliente = genai.Client(api_key="Chave_api")
response = cliente.models.generate_content(
    model="gemini-2.0-flash",
    contents="Ola"
)

print(response.text)