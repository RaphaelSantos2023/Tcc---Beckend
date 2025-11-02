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
from google import genai

load_dotenv()

cliente = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")  # Troque para algo seguro

db_config = {
    'host': os.getenv("DB_HOST") ,
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'database': os.getenv("DB_NAME")
}

ALLOWED_EXTENSIONS = {'pdf', 'ppt', 'pptx', 'doc', 'docx'}

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            parts = request.headers['Authorization'].split()
            if len(parts) == 2 and parts[0] == 'Bearer':
                token = parts[1]

        if not token:
            return jsonify({'message': 'Token está faltando!'}), 401

        conn = None
        cursor = None  # ← inicializa aqui

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user_id = data['id_usuario']

            # Buscar tipo_usuario no banco para o usuário autenticado
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT tipo_usuario FROM usuarios WHERE id_usuario = %s AND ativo = TRUE", (current_user_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({'message': 'Usuário não encontrado ou inativo.'}), 401

            current_user_role = user['tipo_usuario']

        except Exception as e:
            return jsonify({'message': 'Token inválido ou expirado!', 'error': str(e)}), 401

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        return f(current_user_id, current_user_role, *args, **kwargs)
    return decorated

def roles_required(*allowed_roles):
    """
    Decorator para limitar acesso a usuários com papeis específicos.
    Uso:
      @roles_required('admin', 'professor')
      def sua_rota(current_user_id, current_user_role):
          ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(current_user_id, current_user_role, *args, **kwargs):
            if current_user_role not in allowed_roles:
                return jsonify({'message': 'Permissão negada para seu nível de usuário.'}), 403
            return f(current_user_id, current_user_role, *args, **kwargs)
        return wrapper
    return decorator

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    print(data)
    if not data:
        return jsonify({'message': 'JSON ausente na requisição.'}), 400

    required_fields = ['email', 'senha', 'nome_completo', 'tipo_usuario']
    if any(field not in data for field in required_fields):
        return jsonify({'message': 'Campos obrigatórios faltando'}), 400

    email = data['email']
    senha = data['senha']
    nome_completo = data['nome_completo']
    tipo_usuario = data.get('tipo_usuario', 'aluno').lower()
    curso_atual = data.get('curso_atual')
    genero = data.get('genero')
    data_nascimento = data.get('data_nascimento')  # YYYY-MM-DD
    
    senha_hash = bcrypt.hash(senha)

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("SELECT id_usuario FROM usuarios WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'message': 'Email já cadastrado'}), 409

        sql_user = """
            INSERT INTO usuarios (email, senha_hash, nome_completo, data_nascimento, genero, curso_atual, tipo_usuario)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql_user, (email, senha_hash, nome_completo, data_nascimento, genero, curso_atual, tipo_usuario))
        conn.commit()
        id_usuario = cursor.lastrowid

        # Se for parceiro (empresa ou faculdade), criar registro na tabela parceiros
        if tipo_usuario == 'parceiro':
            tipo_parceiro = data.get('tipo_parceiro')  # 'empresa' ou 'faculdade'
            nome_fantasia = data.get('nome_fantasia')
            razao_social = data.get('razao_social')
            cnpj = data.get('cnpj')

            if not tipo_parceiro or tipo_parceiro not in ['empresa', 'faculdade']:
                return jsonify({'message': 'Tipo de parceiro inválido ou ausente'}), 400

            telefone = data.get('telefone')
            site = data.get('site')
            email_parceiro = data.get('email_parceiro', email)  # usa o mesmo email do usuário, se não enviado outro

            sql_parceiro = """
                INSERT INTO parceiros (
                    id_usuario, tipo_parceiro, nome_fantasia, razao_social, cnpj,
                    telefone, email, site
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_parceiro, (
                id_usuario,
                tipo_parceiro,
                nome_fantasia,
                razao_social,
                cnpj,
                telefone,
                email_parceiro,
                site
            ))

            conn.commit()
        # Se for professor, criar entrada na tabela dados_professor
        if tipo_usuario == 'professor':
            formacao = data.get('formacao')
            area_atuacao = data.get('area_atuacao')
            tempo_experiencia = data.get('tempo_experiencia')

            sql_dados_prof = """
                INSERT INTO dados_professor (id_usuario, formacao, area_atuacao, tempo_experiencia)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql_dados_prof, (id_usuario, formacao, area_atuacao, tempo_experiencia))
            conn.commit()
        
        # Se veio endereço no JSON, salvar na tabela de endereços
        endereco = data.get('endereco')
        if endereco:
            sql_endereco = """
                INSERT INTO enderecos (
                    id_usuario, cep, logradouro, numero, complemento,
                    bairro, cidade, estado, pais, tipo_endereco
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_endereco, (
                id_usuario,
                endereco.get('cep'),
                endereco.get('logradouro'),
                endereco.get('numero'),
                endereco.get('complemento'),
                endereco.get('bairro'),
                endereco.get('cidade'),
                endereco.get('estado'),
                endereco.get('pais', 'Brasil'),
                endereco.get('tipo_endereco', 'residencial')
            ))
            conn.commit()

        return jsonify({'message': 'Usuário registrado com sucesso', 'id_usuario': id_usuario}), 201

    except mysql.connector.Error as err:
        print("Erro MySQL:", err)
        return jsonify({'message': 'Erro no banco de dados', 'error': str(err)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/gemini/query', methods=['POST'])
@token_required   # só logado
def gemini_query(current_user_id, current_user_role):
    data = request.get_json()
    print(f"data: {data}")
    prompt = data.get("prompt")
    print(f"prompt: {prompt}")
    if not prompt:
        return jsonify({"error": "Prompt é obrigatório"}), 400

    try:
        # 🔹 Buscar perfil acadêmico do usuário para enriquecer o prompt
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT periodo_atual, ira_geral, interesses_principais, habilidades, objetivo_carreira
            FROM perfis_academicos
            WHERE id_usuario = %s
        """, (current_user_id,))
        perfil = cursor.fetchone()
        print(f"perfil: {perfil}")
        # Se não tiver perfil acadêmico, não dá erro, mas gera resposta só com prompt
        contexto_extra = ""
        if perfil:
            contexto_extra = f"""
            O usuário está no período {perfil['periodo_atual']}, com IRA {perfil['ira_geral']}.
            Seus interesses são: {perfil['interesses_principais']}.
            Habilidades: {perfil['habilidades']}.
            Objetivo de carreira: {perfil['objetivo_carreira']}.
            """
            print(f"> contexto_extra: {contexto_extra}")

        # 🔹 Monta prompt final para o Gemini
        prompt_final = f"""
        Usuário fez a seguinte pergunta: "{prompt}"
        {contexto_extra}
        Gere uma resposta útil, personalizada ao contexto acadêmico/profissional do usuário.
        """

        response = cliente.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt_final
        )

        print(response.text)

        resposta_texto = response.text  # não .text

        print(f"resposta_texto: {resposta_texto}")

        return jsonify({
            "prompt": prompt,
            "response": resposta_texto,
            "contexto_usado": bool(perfil)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('email') or not data.get('senha'):
        return jsonify({'message': 'Email e senha são obrigatórios'}), 400

    email = data['email']
    senha = data['senha']

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # 🔹 Buscar id_usuario, senha_hash e tipo_usuario
        cursor.execute("""
            SELECT id_usuario, senha_hash, tipo_usuario
            FROM usuarios
            WHERE email = %s AND ativo = TRUE
        """, (email,))
        user = cursor.fetchone()

        if not user or not bcrypt.verify(senha, user['senha_hash']):
            return jsonify({'message': 'Usuário ou senha incorretos'}), 401

        token = jwt.encode({
            'id_usuario': user['id_usuario'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        }, app.config['SECRET_KEY'], algorithm="HS256")

        # 🔹 Retornar também tipo_usuario
        return jsonify({
            'token': token,
            'tipo_usuario': user['tipo_usuario']
        })

    except mysql.connector.Error as err:
        return jsonify({'message': 'Erro no banco de dados', 'error': str(err)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/admin-area', methods=['GET'])
@token_required
@roles_required('admin')
def admin_area(current_user_id, current_user_role):
    return jsonify({'message': f'Bem-vindo ao painel admin, usuário {current_user_id}!'})

@app.route('/professor-area', methods=['GET'])
@token_required
@roles_required('admin', 'professor')
def professor_area(current_user_id, current_user_role):
    return jsonify({'message': f'Área de professores, usuário {current_user_id} com papel {current_user_role}.'})

@app.route('/aluno-area', methods=['GET'])
@token_required
@roles_required('aluno', 'professor', 'admin')
def aluno_area(current_user_id, current_user_role):
    return jsonify({'message': f'Área de alunos para usuário {current_user_id}.'})

@app.route('/logout', methods=['POST'])
@token_required
def logout(current_user_id, current_user_role):
    # Logout básico (JWT stateless)
    return jsonify({'message': 'Logout realizado com sucesso.'})

@app.route('/alunos', methods=['GET'])
@token_required
@roles_required('admin', 'professor')  # Somente admins e professores podem acessar
def listar_alunos(current_user_id, current_user_role):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id_usuario, nome_completo, email, curso_atual, data_nascimento, genero
            FROM usuarios
            WHERE tipo_usuario = 'aluno' AND ativo = TRUE
        """)
        alunos = cursor.fetchall()

        return jsonify({'alunos': alunos})

    except mysql.connector.Error as err:
        print("Erro MySQL:", err)
        return jsonify({'message': 'Erro ao buscar alunos', 'error': str(err)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/parceiros', methods=['GET'])
@token_required
@roles_required('admin', 'professor')
def listar_parceiros(current_user_id, current_user_role):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT p.id_parceiro, u.nome_completo AS responsavel, u.email, p.tipo_parceiro,
                   p.nome_fantasia, p.razao_social, p.cnpj
            FROM parceiros p
            JOIN usuarios u ON p.id_usuario = u.id_usuario
            WHERE u.ativo = TRUE
        """)
        parceiros = cursor.fetchall()
        return jsonify({'parceiros': parceiros})

    except mysql.connector.Error as err:
        return jsonify({'message': 'Erro ao buscar parceiros', 'error': str(err)}), 500

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/parceiro-area', methods=['GET'])
@token_required
@roles_required('parceiro', 'admin')
def parceiro_area(current_user_id, current_user_role):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Buscar os dados do parceiro
        cursor.execute("""
            SELECT p.id_parceiro, p.tipo_parceiro, p.nome_fantasia, p.razao_social, p.cnpj
            FROM parceiros p
            WHERE p.id_usuario = %s
        """, (current_user_id,))
        parceiro = cursor.fetchone()

        if not parceiro:
            return jsonify({'message': 'Parceiro não encontrado'}), 404

        return jsonify({'message': f'Bem-vindo, parceiro!', 'parceiro': parceiro})

    except mysql.connector.Error as err:
        return jsonify({'message': 'Erro no painel do parceiro', 'error': str(err)}), 500

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

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
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO foruns (nome, descricao, criado_por)
            VALUES (%s, %s, %s)
        """, (nome, descricao, current_user_id))
        conn.commit()

        return jsonify({'message': 'Fórum criado com sucesso!'}), 201
    finally:
        cursor.close()
        conn.close()

@app.route('/forum', methods=['GET'])
@token_required
def listar_foruns(current_user_id, current_user_role):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT f.id_forum, f.nome, f.descricao, f.data_criacao, u.nome_completo AS criador
            FROM foruns f
            LEFT JOIN usuarios u ON f.criado_por = u.id_usuario
            ORDER BY f.data_criacao DESC
        """)
        foruns = cursor.fetchall()
        return jsonify({'foruns': foruns})
    finally:
        cursor.close()
        conn.close()

@app.route('/forum/<int:id_forum>/publicar', methods=['POST'])
@token_required
@roles_required('aluno', 'professor', 'admin')
def publicar_post(current_user_id, current_user_role, id_forum):
    data = request.get_json()
    titulo = data.get('titulo')
    conteudo = data.get('conteudo')
    categoria = data.get('categoria')
    print(f"id_forum: {id_forum}")
    if not titulo or not conteudo:
        return jsonify({'message': 'Título e conteúdo são obrigatórios.'}), 400

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO publicacoes_forum (id_usuario, titulo, conteudo, categoria,id_forum)
            VALUES (%s, %s, %s, %s, %s)
        """, (current_user_id, titulo, conteudo, categoria,id_forum))
        conn.commit()

        return jsonify({'message': 'Publicação criada com sucesso!'}), 201
    finally:
        cursor.close()
        conn.close()

@app.route('/forum/<int:id_forum>/publicacoes', methods=['GET'])
@token_required
def listar_publicacoes(current_user_id, current_user_role, id_forum):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT p.id_publicacao, p.titulo, p.conteudo, p.categoria, p.data_criacao,
                   u.nome_completo AS autor
            FROM publicacoes_forum p
            JOIN usuarios u ON p.id_usuario = u.id_usuario
            WHERE p.id_forum = %s
            ORDER BY p.data_criacao DESC
        """, (id_forum,))
        posts = cursor.fetchall()
        return jsonify({'publicacoes': posts})
    finally:
        cursor.close()
        conn.close()

@app.route('/materiais/upload', methods=['POST'])
@token_required
@roles_required('professor', 'parceiro', 'admin')  # só estes podem enviar
def upload_material(current_user_id, current_user_role):
    if 'arquivo' not in request.files:
        return jsonify({'message': 'Nenhum arquivo enviado'}), 400

    file = request.files['arquivo']
    if file.filename == '':
        return jsonify({'message': 'Nenhum arquivo selecionado'}), 400

    if not allowed_file(file.filename):
        return jsonify({'message': 'Tipo de arquivo não permitido'}), 400

    filename = secure_filename(file.filename)
    caminho = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(caminho)

    titulo = request.form.get('titulo')
    descricao = request.form.get('descricao', '')
    tipo_material = request.form.get('tipo_material', 'outro')
    assunto = request.form.get('tipo', '')  # 🔹 novo campo "assunto"

    if not titulo:
        return jsonify({'message': 'Título é obrigatório'}), 400

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO materiais (id_usuario, titulo, descricao, tipo_material, tipo, caminho_arquivo)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (current_user_id, titulo, descricao, tipo_material, assunto, caminho))
        conn.commit()

        return jsonify({'message': 'Material enviado com sucesso!'}), 201

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/materiais', methods=['GET'])
@token_required
def listar_materiais(current_user_id, current_user_role):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT m.id_material, m.titulo, m.descricao, m.tipo_material, m.caminho_arquivo, u.nome_completo AS autor
        FROM materiais m
        JOIN usuarios u ON m.id_usuario = u.id_usuario
        ORDER BY m.data_upload DESC
    """)
    materiais = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({'materiais': materiais})

@app.route('/materiais/buscar', methods=['GET'])
@token_required
def buscar_materiais(current_user_id, current_user_role):
    """
    Busca materiais pelo título ou assunto.
    Exemplo de requisição: /materiais/buscar?query=matematica
    """
    query = request.args.get('query', '').strip()

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        if query:
            search_query = f"%{query}%"
            cursor.execute("""
                SELECT m.id_material, m.titulo, m.descricao, m.tipo_material, m.tipo AS assunto,
                       m.caminho_arquivo, u.nome_completo AS autor
                FROM materiais m
                JOIN usuarios u ON m.id_usuario = u.id_usuario
                WHERE m.titulo LIKE %s OR m.tipo LIKE %s
                ORDER BY m.data_upload DESC
            """, (search_query, search_query))
        else:
            cursor.execute("""
                SELECT m.id_material, m.titulo, m.descricao, m.tipo_material, m.tipo AS assunto,
                       m.caminho_arquivo, u.nome_completo AS autor
                FROM materiais m
                JOIN usuarios u ON m.id_usuario = u.id_usuario
                ORDER BY m.data_upload DESC
            """)

        materiais = cursor.fetchall()
        return jsonify({'materiais': materiais})

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/uploads/<filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
