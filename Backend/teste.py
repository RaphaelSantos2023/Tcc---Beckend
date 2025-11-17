from flask import Flask, request, jsonify,send_from_directory
import mysql.connector
from passlib.hash import bcrypt
import jwt
import datetime
from functools import wraps
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
from supabase import create_client, Client
from google import genai

load_dotenv()

cliente = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")  # Troque para algo seguro

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase = create_client(url,key)

email = "email"
senha = "senha"
usuario = supabase.auth.sign_up(email=email,password=senha)


email = "email"
senha = "senha"
sessao = supabase.auth.sign_in(email=email,password=senha)

#data = supabase.table("usuarios").insert({"email": "joao.almeida@email.com","senha_hash": "$2b$12$PbJ4R9gp8E4FhVxQZTwFqut0sgC8EWPqv4aiE0P48ocxpR29gkZz6","nome_completo": "João Almeida","data_nascimento": "2002-05-14","genero": "Masculino","curso_atual": "Engenharia da Computação","tipo_usuario": "aluno","ativo": True}).execute()

#data = supabase.table("usuarios").select("*").execute()


#print(data)