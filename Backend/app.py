from flask import Flask, request, send_file, jsonify,send_from_directory
from functools import wraps
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import tempfile
from flask_bcrypt import Bcrypt
from jwt import decode, InvalidTokenError
from supabase import create_client, Client
from google import genai
load_dotenv()

cliente = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")  

bcrypt = Bcrypt(app)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase = create_client(url,key)

ALLOWED_EXTENSIONS = {'pdf', 'ppt', 'pptx', 'doc', 'docx'}

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def Get_Usuario(id):
        return supabase.table("usuarios").select("*").eq("auth_id",id).execute()

def Get_auth_id(id):
        resp =  supabase.table("usuarios").select("auth_id").eq("id_usuario",id).execute()
        return resp.data[0].get("auth_id")

def getnome(id):
        resp =  supabase.table("usuarios").select("nome_completo").eq("id_usuario",id).execute()
        return resp.data[0]["nome_completo"]

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if "Authorization" in request.headers:
            parts = request.headers["Authorization"].split()
            if len(parts) == 2 and parts[0] == "Bearer":
                token = parts[1]

        if not token:
            return jsonify({"message": "Token está faltando!"}), 401

        try:
            # 🔥 decodifica localmente (sem chamar Supabase)
            payload = decode(token, options={"verify_signature": False})
            auth_id = payload.get("sub")

            if not auth_id:
                return jsonify({"message": "Token inválido!"}), 401

            usuario_resp = supabase.table("usuarios") \
                .select("id_usuario, tipo_usuario") \
                .eq("auth_id", auth_id) \
                .eq("ativo", True) \
                .execute()

            if not usuario_resp.data:
                return jsonify({"message": "Usuário não encontrado!"}), 401

            current_user_id = usuario_resp.data[0]["id_usuario"]
            current_user_role = usuario_resp.data[0]["tipo_usuario"]

        except Exception as e:
            print("ERRO TOKEN:", e)
            return jsonify({"message": "Erro ao validar token", "error": str(e)}), 401

        return f(current_user_id, current_user_role, *args, **kwargs)

    return decorated

def roles_required(*roles_permitidos):
    def decorator(func):
        @wraps(func)
        def wrapper(current_user_id, current_user_role, *args, **kwargs):

            if current_user_role not in roles_permitidos:
                return jsonify({"message": "Acesso negado."}), 403

            return func(current_user_id, current_user_role, *args, **kwargs)
        return wrapper
    return decorator


@app.route('/cursos', methods=['GET'])
@token_required
def listar_cursos(current_user_id, current_user_role):
    """Lista todos os cursos disponíveis (todos podem ver)."""
    print("User ID:", current_user_id)
    print("User Role:", current_user_role)

    try:
        response = supabase.table("cursos_extracurriculares") \
            .select("id_cursos, nome, descricao, carga_horaria, link_acesso, criado_por") \
            .order("nome", desc=False) \
            .execute()

        cursos = response.data  # já vem como lista de dicionários

        return jsonify({"cursos": cursos}), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/cursos/criar', methods=['POST'])
@token_required
@roles_required('professor', 'parceiro', 'admin')
def criar_curso(current_user_id, current_user_role):
    """Criação de curso — permitido para todos exceto alunos."""

    data = request.get_json()
    nome = data.get('nome')
    descricao = data.get('descricao')
    carga_horaria = data.get('carga_horaria', 0)
    link_acesso = data.get('link_acesso')

    if not nome or not descricao or not link_acesso or not carga_horaria :
        return jsonify({"message": "Nome e descrição são obrigatórios!"}), 400
    print(f"current_user_id: {current_user_id}")
    try:
        response = supabase.table("cursos_extracurriculares").insert({
            "nome": nome,
            "descricao": descricao,
            "carga_horaria": carga_horaria,
            "link_acesso": link_acesso,
            "criado_por": current_user_id
        }).execute()
        print("tudo certo")
        return jsonify({
            "message": "Curso criado com sucesso!",
            "curso": response.data  # Já retorna o registro inserido
        }), 201

    except Exception as e:
        print(f"Erro na criação de curso: {str(e)}")
        return jsonify({"erro": str(e)}), 500

@app.route('/cursos/<int:id_curso>', methods=['PUT'])
@token_required
@roles_required('professor', 'parceiro', 'admin')
def editar_curso(current_user_id, current_user_role, id_curso):
    """Edição de curso — permitido para todos exceto alunos."""

    data = request.get_json()

    # 🔥 Montagem dinâmica dos campos a atualizar
    campos = {
        "nome": data.get("nome"),
        "descricao": data.get("descricao"),
        "carga_horaria": data.get("carga_horaria"),
        "link_acesso": data.get("link_acesso"),
    }

    # Remove valores None para não sobrescrever
    campos = {k: v for k, v in campos.items() if v is not None}

    if not campos:
        return jsonify({"message": "Nenhum campo enviado para atualização"}), 400

    try:
        response = supabase.table("cursos_extracurriculares") \
            .update(campos) \
            .eq("id_cursos", id_curso) \
            .execute()

        # Se não atualizou nada → curso não existe
        if not response.data:
            return jsonify({"message": "Curso não encontrado"}), 404

        return jsonify({
            "message": "Curso atualizado com sucesso!",
            "curso": response.data     # já retorna o registro atualizado
        }), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/cursos/<int:id_curso>', methods=['DELETE'])
@token_required
@roles_required('professor', 'parceiro', 'admin')
def deletar_curso(current_user_id, current_user_role, id_curso):
    """Exclusão de curso — permitido para todos exceto alunos."""

    try:
        response = supabase.table("cursos_extracurriculares") \
            .delete() \
            .eq("id_cursos", id_curso) \
            .execute()

        # Se não removeu nada → curso não existe
        if not response.data:
            return jsonify({"message": "Curso não encontrado"}), 404

        return jsonify({"message": "Curso removido com sucesso!"}), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/cursos/inscrever', methods=['POST'])
@token_required
@roles_required('aluno')
def inscrever_curso(current_user_id, current_user_role):
    """Inscrição em curso — apenas alunos podem."""
    data = request.get_json()
    id_curso = data.get("id_curso")

    if not id_curso:
        return jsonify({"message": "É necessário informar id_curso"}), 400

    try:
        response = supabase.table("Curso_Usuario").insert({
            "id_usuario": current_user_id,
            "id_cursos": id_curso,
            "porcentagem_completada": 0
        }).execute()

        return jsonify({
            "message": "Inscrição realizada com sucesso!",
            "registro": response.data   # já retorna a linha inserida
        }), 201

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ============================
# ROTAS PARA TEMAS DE TCC
# ============================

@app.route('/temas', methods=['GET'])
@token_required
def listar_temas(current_user_id, current_user_role):
    """Todos podem visualizar temas de TCC."""
    try:
        response = supabase.table("tema_tcc") \
            .select("*") \
            .order("data_criacao", desc=True) \
            .execute()

        temas = []

        for row in response.data:
            nome_criador = getnome(row['criado_por'])
            temas.append({
                "id_tema": row["id_tema"],
                "titulo": row["titulo"],
                "descricao": row["descricao"],
                "area_conhecimento": row["area_conhecimento"],
                "data_criacao": row["data_criacao"],
                "criado_por": nome_criador
            })

        return jsonify({"temas": temas})

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route('/temas/criar', methods=['POST'])
@token_required
@roles_required('professor', 'parceiro', 'admin')
def criar_tema(current_user_id, current_user_role):
    """Professores, parceiros e admins podem propor temas de TCC."""
    data = request.get_json()
    nome = data.get('titulo')  # ainda vem como titulo do front
    descricao = data.get('descricao')
    area_conhecimento = data.get('area_conhecimento')

    if not nome:
        return jsonify({'message': 'Título (nome) é obrigatório.'}), 400

    try:
        resposta = supabase.table("tema_tcc").insert({
            "titulo": nome,
            "descricao":descricao,
            "area_conhecimento": area_conhecimento,
            "criado_por": current_user_id
        }).execute()

        if not resposta.data:
            return jsonify({"message": "Erro ao criar tema."}), 404

        return jsonify({"message": "Tema de TCC criado com sucesso!"}), 201

    except Exception as e:
        return jsonify({"message": "Erro no servidor", "error": str(e)}), 500
    


@app.route('/temas/<int:id_tema>', methods=['DELETE'])
@token_required
@roles_required('professor', 'parceiro', 'admin')
def excluir_tema(current_user_id, current_user_role, id_tema):
    """Permite excluir tema de TCC (exceto alunos)."""
    try:
        resposta = supabase.table("tema_tcc") \
            .delete() \
            .eq("id_tema", id_tema) \
            .execute()

        # Se não encontrou nenhum registro
        if resposta.data == []:
            return jsonify({"message": "Tema não encontrado."}), 404

        # Se o Supabase retornou erro explícito
        if not resposta.data:
            return jsonify({"message": "Erro ao remover tema."}), 404

        return jsonify({"message": "Tema de TCC removido com sucesso!"}), 200

    except Exception as e:
        return jsonify({"message": "Erro interno no servidor", "error": str(e)}), 500

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data:
        return jsonify({'message': 'JSON ausente na requisição.'}), 400

    required_fields = ['email', 'senha', 'nome_completo', 'tipo_usuario']
    if any(field not in data for field in required_fields):
        return jsonify({'message': 'Campos obrigatórios faltando'}), 400

    email = data['email']
    senha = data['senha']
    nome_completo = data['nome_completo']
    tipo_usuario = data['tipo_usuario'].lower()
    curso_atual = data.get('curso_atual')
    genero = data.get('genero')
    data_nascimento = data.get('data_nascimento')

    try:
        # ===== 1️⃣ CRIA USUÁRIO NO SUPABASE AUTH =====
        auth_res = supabase.auth.sign_up({"email": email, "password": senha})

        if auth_res.user is None:
            return jsonify({'message': 'Erro ao registrar usuário no Supabase'}), 500

        # ===== 2️⃣ GERAR HASH DA SENHA =====
        # converte para string para salvar no banco

        # ===== 3️⃣ SALVAR USUÁRIO NA TABELA usuarios =====
        resp = supabase.table("usuarios").insert({
            "email": email,
            "nome_completo": nome_completo,
            "curso_atual": curso_atual,
            "genero": genero,
            "data_nascimento": data_nascimento,
            "tipo_usuario": tipo_usuario,
            "senha_hash": senha,
            "auth_id": auth_res.user.id
        }).execute()

        if not resp.data:
            return jsonify({
                "message": "Erro ao criar usuário"
            }), 404

        # ===== 4️⃣ SE FOR PARCEIRO: TABELA parceiros =====
        if tipo_usuario == "parceiro":
            tipo_parceiro = data.get("tipo_parceiro")
            if tipo_parceiro not in ["empresa", "faculdade"]:
                return jsonify({'message': 'Tipo de parceiro inválido'}), 400

            supabase.table("parceiros").insert({
                "tipo_parceiro": tipo_parceiro,
                "nome_fantasia": data.get("nome_fantasia"),
                "razao_social": data.get("razao_social"),
                "cnpj": data.get("cnpj"),
                "telefone": data.get("telefone"),
                "email": data.get("email_parceiro", email),
                "site": data.get("site")
            }).execute()

        # ===== 5️⃣ PROFESSOR =====
        if tipo_usuario == "professor":
            supabase.table("dados_professor").insert({
                "formacao": data.get("formacao"),
                "area_atuacao": data.get("area_atuacao"),
                "tempo_experiencia": data.get("tempo_experiencia")
            }).execute()

        # ===== 6️⃣ ENDEREÇO =====
        endereco = data.get("endereco")
        if endereco:
            usuario_id = resp.data[0]['id']
            print("antes de endereco")
            supabase.table("enderecos").insert({
                "id_usuario": usuario_id,
                "cep": endereco.get("cep"),
                "logradouro": endereco.get("logradouro"),
                "numero": endereco.get("numero"),
                "complemento": endereco.get("complemento"),
                "bairro": endereco.get("bairro"),
                "cidade": endereco.get("cidade"),
                "estado": endereco.get("estado"),
                "pais": endereco.get("pais", "Brasil"),
                "tipo_endereco": endereco.get("tipo_endereco", "residencial")
            }).execute()
            print("antes de endereco 60911cf6-ddd8-49f3-90bc-40b24180da0d")

        return jsonify({"message": "Usuário registrado com sucesso"}), 201

    except Exception as e:
        print(str(e))
        return jsonify({
            "message": "Erro no servidor",
            "error": str(e)
        }), 500

# ... (imports, app setup, supabase setup, bcrypt, etc.)

@app.route('/register/parceiro', methods=['POST'])
def cadastrar_parceiro():
    """
    Cadastra um novo usuário do tipo 'parceiro' na tabela 'usuarios'
    e adiciona seus dados específicos na tabela 'parceiros'.
    """
    data = request.get_json()

    # 1. Validar e coletar dados básicos do usuário (tabela 'usuarios')
    email = data.get('email')
    senha = data.get('senha')
    nome_completo = data.get('nome_completo')
    curso_atual = data.get('curso_atual', 'N/A') # Exigido no seu schema, mas pode ser 'N/A' para parceiros
    data_nascimento = data.get('data_nascimento')
    genero = data.get('genero')
    auth_id = data.get('auth_id') # Se estiver usando Supabase Auth (opcional)

    # 2. Coletar dados específicos do parceiro (tabela 'parceiros')
    tipo_parceiro = data.get('tipo_parceiro') # 'faculdade' ou 'empresa'
    nome_fantasia = data.get('nome_fantasia')
    razao_social = data.get('razao_social')
    cnpj = data.get('cnpj')
    telefone = data.get('telefone')
    email_parceiro = data.get('email_parceiro')
    site = data.get('site')
    
    # 3. Validação Mínima
    if not email or not senha or not nome_completo or not tipo_parceiro or not cnpj:
        return jsonify({"message": "Dados obrigatórios (email, senha, nome_completo, tipo_parceiro, cnpj) ausentes"}), 400

    if tipo_parceiro not in ['faculdade', 'empresa']:
        return jsonify({"message": "Tipo de parceiro inválido. Use 'faculdade' ou 'empresa'."}), 400
        
    try:
        # 4. Criptografar Senha
        senha_hash = senha

        # 5. Inserir na Tabela 'usuarios'
        usuario_data = {
            "email": email,
            "senha_hash": senha_hash,
            "nome_completo": nome_completo,
            "data_nascimento": data_nascimento,
            "genero": genero,
            "curso_atual": curso_atual,
            "tipo_usuario": "parceiro", # CHAVE: Definir o tipo correto
            "auth_id": auth_id
        }
        
        # A inserção retorna uma lista de resultados. Usamos [0] para pegar o objeto inserido.
        result_usuario = supabase.table("usuarios").insert(usuario_data).execute()
        novo_usuario = result_usuario.data[0]
        id_usuario = novo_usuario['id_usuario']

        # 6. Inserir na Tabela 'parceiros'
        parceiro_data = {
            "id_usuario": id_usuario,
            "tipo_parceiro": tipo_parceiro,
            "nome_fantasia": nome_fantasia,
            "razao_social": razao_social,
            "cnpj": cnpj,
            "telefone": telefone,
            "email": email_parceiro or email, # Usa o email de parceiro ou o email de login
            "site": site
        }
        
        supabase.table("parceiros").insert(parceiro_data).execute()

        return jsonify({
            "message": "Parceiro cadastrado com sucesso!",
            "id_usuario": id_usuario,
            "email": email
        }), 201

    except Exception as e:
        print("ERRO SUPABASE →", str(e))
        # Se houver um erro, é bom tentar limpar o registro de 'usuarios' se ele foi criado,
        # mas para simplificação, vamos apenas reportar o erro.
        if "Duplicate key" in str(e):
             return jsonify({"message": "Erro ao cadastrar parceiro", "error": "Email ou CNPJ já cadastrado."}), 409
        return jsonify({"message": "Erro ao cadastrar parceiro", "error": str(e)}), 500

# ... (outras rotas)

@app.route('/perfil', methods=['POST'])
@token_required
@roles_required('aluno', 'professor')
def criar_ou_atualizar_perfil(current_user_id, current_user_role):
    data = request.get_json()

    if not data:
        return jsonify({'message': 'JSON ausente'}), 400

    required_fields = ["periodo_atual", "ira_geral", "interesses_principais", "habilidades", "objetivo_carreira"]
    if any(f not in data for f in required_fields):
        return jsonify({"message": "Campos obrigatórios faltando"}), 400

    payload = {
        "id_usuario": current_user_id,
        "periodo_atual": data["periodo_atual"],
        "ira_geral": data["ira_geral"],
        "interesses_principais": data["interesses_principais"],
        "habilidades": data["habilidades"],
        "objetivo_carreira": data["objetivo_carreira"]
    }

    # UPSERT = INSERT ou UPDATE AUTOMÁTICO
    response = supabase.table("perfis_academicos").upsert(payload).execute()

    if not response.data:
        return jsonify({"message": "Erro ao salvar perfil"}), 404

    return jsonify({"message": "Perfil acadêmico salvo com sucesso!"}), 200

@app.route('/perfil', methods=['GET'])
@token_required
def get_perfil(current_user_id, current_user_role):
    response = (
        supabase
        .table("perfis_academicos")
        .select("*")
        .eq("id_usuario", current_user_id)
        .single()
        .execute()
    )

    if not response.data:
        return jsonify({"message": "Nenhum perfil encontrado"}), 404

    return jsonify({"perfil": response.data}), 200

@app.route('/gemini/query', methods=['POST'])
@token_required
def gemini_query(current_user_id, current_user_role):

    id_usado = current_user_id
    data = request.get_json()
    prompt = data.get("prompt")

    if not prompt:
        return jsonify({"error": "Prompt é obrigatório"}), 400

    try:
        # 🔹 Busca perfil acadêmico no Supabase
        perfil_resp = (
            supabase.table("perfis_academicos")
            .select("periodo_atual, ira_geral, interesses_principais, habilidades, objetivo_carreira")
            .eq("id_usuario", id_usado)
            .execute()
        )

        perfil = perfil_resp.data

        contexto_extra = ""
        if perfil:
            contexto_extra = f"""
            O usuário está no período {perfil['periodo_atual']}, com IRA {perfil['ira_geral']}.
            Interesses: {perfil['interesses_principais']}.
            Habilidades: {perfil['habilidades']}.
            Objetivo de carreira: {perfil['objetivo_carreira']}.
            """

        # 🔹 Monta prompt final
        prompt_final = f"""
        Usuário perguntou: "{prompt}"
        {contexto_extra}
        Gere uma resposta personalizada, útil e voltada à trajetória acadêmica e profissional do usuário.
        """
        # 🔹 Gera resposta com Gemini
        response = cliente.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt_final
        )
        resposta_texto = response.text.strip()

        # 🔹 Salva recomendação no SUPABASE
        insert_resp = (
            supabase.table("recomendacoes")
            .insert({
                "id_usuario": id_usado,
                "prompt": prompt,
                "resposta": resposta_texto
            })
            .execute()
        )

        if not insert_resp.data:
            return jsonify({"error": "Falha ao inserir recomendação no banco!"}), 404
        
        return jsonify({
            "id_recomendacao": insert_resp.data[0]["id_recomendacao"],  # se sua tabela usa id SERIAL
            "prompt": prompt,
            "resposta": resposta_texto,
            "contexto_usado": perfil is not None,
            "message": "Recomendação gerada e salva com sucesso!"
        }), 200

    except Exception as e:
        print(f"erro por que aconteceu algo:{str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/recomendacoes/<int:id_recomendacao>/avaliar', methods=['POST'])
@token_required
def avaliar_recomendacao(current_user_id, current_user_role, id_recomendacao):
    data = request.get_json()
    nota = data.get('nota')
    comentario = data.get('comentario')

    # 🔹 Validação da nota
    if nota is None or not (1 <= int(nota) <= 5):
        return jsonify({'message': 'A nota deve ser de 1 a 5.'}), 400

    try:
        # 🔹 Verifica se a recomendação existe
        rec_resp = (
            supabase.table("recomendacoes")
            .select("id_recomendacao")
            .eq("id_recomendacao", id_recomendacao)
            .execute()
        )

        if rec_resp.data is None:
            return jsonify({"message": "Recomendação não encontrada."}), 404

        # 🔹 Insere avaliação
        insert_resp = (
            supabase.table("avaliacoes_recomendacao")
            .insert({
                "id_recomendacao": id_recomendacao,
                "id_usuario": current_user_id,
                "nota": nota,
                "comentario": comentario
            })
            .execute()
        )

        if not insert_resp:
            return jsonify({"message": "erro de insert"}), 404

        return jsonify({"message": "Avaliação registrada com sucesso!"}), 201

    except Exception as e:
        print(f"erro ao avaliar: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/recomendacoes', methods=['GET'])
@token_required
def listar_recomendacoes(current_user_id, current_user_role):

    try:
        # 🔹 Busca as recomendações do usuário
        response = supabase.table("recomendacoes") \
            .select("id_recomendacao, prompt, resposta, data_geracao") \
            .eq("id_usuario", current_user_id) \
            .order("data_geracao", desc=True) \
            .execute()

        # Se a query falhar
        if not response.data:
            return jsonify({"messagge": "erro de response"}), 404

        return jsonify({"recomendacoes": response.data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('email') or not data.get('senha'):
        return jsonify({'message': 'Email e senha são obrigatórios'}), 400

    email = data['email']
    senha = data['senha']
    try:
        # 🔹 Login pelo Supabase Auth
        resp = supabase.auth.sign_in_with_password({
            "email": email,
            "password": senha
        })

        if not resp.user:
            return jsonify({'message': 'Usuário ou senha incorretos'}), 401
        
        user_id = resp.user.id     # ID AUTÊNTICO DO SUPABASE
        token_supabase = resp.session.access_token  # Token JWT gerado pelo Supabase

        # 🔹 Buscar tipo_usuario na tabela do projeto (caso você tenha essa coluna separada)
        tipo_resp = supabase.table("usuarios") \
            .select("tipo_usuario") \
            .eq("auth_id", user_id)\
            .execute()

        tipo_usuario = tipo_resp.data[0]["tipo_usuario"] if tipo_resp.data else "aluno"

        return jsonify({
            "token": token_supabase,
            "tipo_usuario": tipo_usuario
        }), 200

    except Exception as e:
        print("ERRO LOGIN:", e)
        return jsonify({"message": "Erro interno no login", "error": str(e)}), 500

@app.route('/admin-area', methods=['GET'])
@token_required     # ⬅ mantém seu validador de token
@roles_required('admin')   # ⬅ mantém a mesma checagem de papel
def admin_area(current_user_id, current_user_role):
    return jsonify({
        "message": f"Bem-vindo ao painel admin, usuário {current_user_id}!"
    }), 200

@app.route('/professor-area', methods=['GET'])
@token_required
@roles_required('admin', 'professor')
def professor_area(current_user_id, current_user_role):
    return jsonify({
        'message': f'Área de professores, usuário {current_user_id} com papel {current_user_role}.'
    }), 200

@app.route('/aluno-area', methods=['GET'])
@token_required
@roles_required('aluno', 'professor', 'admin')
def aluno_area(current_user_id, current_user_role):
    return jsonify({
        'message': f'Área de alunos para usuário {current_user_id}.'
    }), 200

@app.route('/logout', methods=['POST'])
@token_required
def logout(current_user_id, current_user_role):
    return jsonify({'message': 'Logout realizado com sucesso.'})

@app.route('/alunos', methods=['GET'])
@token_required
@roles_required('admin', 'professor')  # Somente admins e professores podem acessar
def listar_alunos(current_user_id, current_user_role):
    try:
        response = supabase.table("usuarios").select(
            "id_usuario, nome_completo, email, curso_atual, data_nascimento, genero"
        ).eq("tipo_usuario", "aluno").eq("ativo", True).execute()

        alunos = response.data

        return jsonify({'alunos': alunos}), 200

    except Exception as e:
        print("Erro Supabase:", e)
        return jsonify({'message': 'Erro ao buscar alunos', 'error': str(e)}), 500


@app.route('/parceiros', methods=['GET'])
@token_required
@roles_required('admin', 'professor')
def listar_parceiros(current_user_id, current_user_role):
    try:
        response = supabase.table("parceiros").select("""
            id_parceiro,
            tipo_parceiro,
            nome_fantasia,
            razao_social,
            cnpj,
            usuarios:usuarios!fk_parceiros_id_usuario(
                nome_completo,
                email,
                ativo
            )
        """).execute()

        parceiros = [
            {
                "id_parceiro": p["id_parceiro"],
                "tipo_parceiro": p["tipo_parceiro"],
                "nome_fantasia": p["nome_fantasia"],
                "razao_social": p["razao_social"],
                "cnpj": p["cnpj"],
                "responsavel": p["usuarios"]["nome_completo"],
                "email": p["usuarios"]["email"],
            }
            for p in response.data
            if p["usuarios"] and p["usuarios"]["ativo"] == True
        ]

        return jsonify({"parceiros": parceiros}), 200

    except Exception as e:
        return jsonify({'message': 'Erro ao buscar parceiros', 'error': str(e)}), 500

@app.route('/forum/criar', methods=['POST'])
@token_required
@roles_required('aluno', 'professor', 'admin', 'parceiro')
def criar_forum(current_user_id, current_user_role):
    data = request.get_json()

    nome = data.get('nome')
    descricao = data.get('descricao')

    if not nome:
        return jsonify({'message': 'Nome do fórum é obrigatório.'}), 400

    try:
        response = supabase.table("foruns").insert({
            "nome": nome,
            "descricao": descricao,
            "criado_por": current_user_id
        }).execute()

        # Se quiser retornar o ID criado
        forum_id = response.data[0]["id_forum"] if response.data else None

        return jsonify({
            "message": "Fórum criado com sucesso!",
            "id_forum": forum_id
        }), 201

    except Exception as e:
        print("ERRO SUPABASE →", str(e))
        return jsonify({"message": "Erro ao criar fórum", "error": str(e)}), 500

@app.route('/forum', methods=['GET'])
@token_required
def listar_foruns(current_user_id, current_user_role):
    
    try:
        response = supabase.table("foruns").select("""
            id_forum,
            nome,
            descricao,
            data_criacao,
            criado_por
        """).order("data_criacao", desc=True).execute()

        foruns = []
        for f in response.data:
            criador_nome = getnome(f.get("criado_por"))
            foruns.append({
                "id_forum": f.get("id_forum"),
                "nome": f.get("nome"),
                "descricao": f.get("descricao"),
                "data_criacao": f.get("data_criacao"),
                "criador": criador_nome
            })

        return jsonify({"foruns": foruns}), 200

    except Exception as e:
        print("ERRO SUPABASE Forum →", str(e))
        return jsonify({"message": "Erro ao listar fóruns", "error": str(e)}), 500

@app.route('/forum/<int:id_forum>/publicar', methods=['POST'])
@token_required
@roles_required('aluno', 'professor', 'admin')
def publicar_post(current_user_id, current_user_role, id_forum):
    data = request.get_json()
    titulo = data.get('titulo')
    conteudo = data.get('conteudo')
    categoria = data.get('categoria')

    if not titulo or not conteudo:
        return jsonify({'message': 'Título e conteúdo são obrigatórios.'}), 400

    try:
        response = supabase.table("publicacoes_forum").insert({
            "id_usuario": current_user_id,
            "titulo": titulo,
            "conteudo": conteudo,
            "categoria": categoria,
            "id_forum": id_forum
        }).execute()

        # Retornar o ID do post criado (opcional, mas útil)
        post_id = response.data[0]["id_publicacao"] if response.data else None

        return jsonify({
            "message": "Publicação criada com sucesso!",
            "id_post": post_id
        }), 201

    except Exception as e:
        print("ERRO SUPABASE →", str(e))
        return jsonify({"message": "Erro ao criar publicação", "error": str(e)}), 500

@app.route('/forum/<int:id_forum>/publicacoes', methods=['GET'])
@token_required
def listar_publicacoes(current_user_id, current_user_role, id_forum):
    try:
        response = supabase.table("publicacoes_forum").select("""
            id_publicacao,
            titulo,
            conteudo,
            categoria,
            data_criacao,
            id_usuario
            )
        """).eq("id_forum", id_forum).order("data_criacao", desc=True).execute()

        publicacoes = []
        for p in response.data:
            autor = getnome(p.get("id_usuario"))
            publicacoes.append({
                "id_publicacao": p.get("id_publicacao"),
                "titulo": p.get("titulo"),
                "conteudo": p.get("conteudo"),
                "categoria": p.get("categoria"),
                "data_criacao": p.get("data_criacao"),
                "autor": autor
            })

        return jsonify({"publicacoes": publicacoes}), 200

    except Exception as e:
        print("ERRO SUPABASE →", str(e))
        return jsonify({"message": "Erro ao listar publicações", "error": str(e)}), 500

@app.route('/materiais/upload', methods=['POST'])
@token_required
@roles_required('professor', 'parceiro', 'admin')
def upload_material(current_user_id, current_user_role):

    if 'arquivo' not in request.files:
        return jsonify({'message': 'Nenhum arquivo enviado'}), 400

    file = request.files['arquivo']
    if file.filename == '':
        return jsonify({'message': 'Nenhum arquivo selecionado'}), 400

    if not allowed_file(file.filename):
        return jsonify({'message': 'Tipo de arquivo não permitido'}), 400

    filename = secure_filename(file.filename)
    try:
        # 🔹 Upload para Supabase Storage (pasta 'materiais')
        file_bytes = file.read()  # lê os bytes do arquivo
        storage_response = supabase.storage.from_('materiais').upload(
            f"{current_user_id}/{filename}",
            file_bytes
        )

        if not storage_response or not storage_response.full_path:
            return jsonify({'message': 'Erro no upload do arquivo'}), 500


        caminho_arquivo = f"materiais/arquivo/{filename}"

        # 🔹 Dados do material
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao', '')
        tipo_material = request.form.get('tipo_material', 'outro')

        if not titulo:
            return jsonify({'message': 'Título é obrigatório'}), 400
        
        auth_id = Get_auth_id(current_user_id)

        # 🔹 Inserir registro na tabela materiais com auth_id (UUID)
        insert_resp = supabase.table("materiais").insert({
            "id_usuario": current_user_id,  # <-- UUID do usuário
            "auth_id": auth_id,
            "titulo": titulo,
            "descricao": descricao,
            "tipo_material": tipo_material,
            "caminho_arquivo": caminho_arquivo
        }).execute()

        if not insert_resp.data:
            return jsonify({'message': 'Erro ao salvar registro no banco'}), 500

        return jsonify({'message': 'Material enviado com sucesso!'}), 201

    except Exception as e:
        print("ERRO SUPABASE →", str(e))
        return jsonify({'message': 'Erro ao enviar material', 'error': str(e)}), 500

@app.route('/materiais', methods=['GET'])
@token_required
def listar_materiais(current_user_id, current_user_role):
    try:
        response = supabase.table("materiais").select("""
            id_material,
            titulo,
            descricao,
            tipo_material,
            caminho_arquivo,
            usuarios:usuarios!fk_materiais_id_usuario(
                nome_completo
            )
        """).order("data_upload", desc=True).execute()

        materiais = []
        for m in response.data:
            usuario = m.get("usuarios")
            autor = usuario.get("nome_completo") if usuario else None
            materiais.append({
                "id_material": m.get("id_material"),
                "titulo": m.get("titulo"),
                "descricao": m.get("descricao"),
                "tipo_material": m.get("tipo_material"),
                "caminho_arquivo": m.get("caminho_arquivo"),
                "autor": autor
            })

        return jsonify({"materiais": materiais}), 200

    except Exception as e:
        print("ERRO SUPABASE →", str(e))
        return jsonify({"message": "Erro ao listar materiais", "error": str(e)}), 500

@app.route('/materiais/buscar', methods=['GET'])
@token_required
def buscar_materiais(current_user_id, current_user_role):
    """
    Busca materiais pelo título ou assunto.
    Exemplo de requisição: /materiais/buscar?query=matematica
    """
    query = request.args.get('query', '').strip()

    try:
        base_query = supabase.table("materiais").select("""
            id_material,
            titulo,
            descricao,
            tipo_material,
            data_upload,
            caminho_arquivo
        """).order("data_upload", desc=True)

        if query:
            # Supabase usa ilike para case-insensitive LIKE
            base_query = base_query.or_(f"titulo.ilike.%{query}%")

        response = base_query.execute()
        materiais = []

        for m in response.data:
            autor = getnome(current_user_id)
            materiais.append({
                "id_material": m.get("id_material"),
                "titulo": m.get("titulo"),
                "descricao": m.get("descricao"),
                "tipo_material": m.get("tipo_material"),
                "assunto": m.get("assunto"),
                "caminho_arquivo": m.get("caminho_arquivo"),
                "autor": autor
            })

        return jsonify({"materiais": materiais}), 200

    except Exception as e:
        print("ERRO SUPABASE →", str(e))
        return jsonify({"message": "Erro ao buscar materiais", "error": str(e)}), 500

@app.route('/materiais/download/<path:filepath>', methods=['GET'])
@token_required
def download_material(current_user_id, current_user_role, filepath):

    try:
        # 🔹 remove prefixo caso venha como "materiais/..."
        filepath = filepath.replace("materiais/", "")

        # 🔹 baixa o binário do Supabase
        file_bytes = supabase.storage.from_("materiais").download(filepath)

        # 🔹 cria arquivo temporário de forma segura
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(file_bytes)
        temp.close()

        # 🔹 envia o arquivo ao navegador
        return send_file(
            temp.name,
            as_attachment=True,
            download_name=os.path.basename(filepath)
        )

    except Exception as e:
        print("ERRO DOWNLOAD →", e)
        return jsonify({"message": "Erro ao baixar material", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
