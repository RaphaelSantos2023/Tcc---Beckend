from google import genai
import os

cliente = genai.Client(api_key="Chave_api")
texto = "ola"

response = cliente.models.generate_content(
    model="gemini-2.0-flash",
    contents=texto
)

print(response.text)