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

@app.route('/cursos', methods=['GET'])
@token_required
def listar_cursos(current_user_id, current_user_role):
    """Lista todos os cursos disponíveis (todos podem ver)."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id_cursos, nome, descricao, carga_horaria, link_acesso, criado_por
        FROM cursos_extracurriculares
        ORDER BY nome ASC
    """)
    cursos = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({'cursos': cursos})


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

    if not nome or not descricao:
        return jsonify({'message': 'Nome e descrição são obrigatórios!'}), 400

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO cursos_extracurriculares (nome, descricao, carga_horaria, link_acesso, criado_por)
        VALUES (%s, %s, %s, %s, %s)
    """, (nome, descricao, carga_horaria, link_acesso, current_user_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Curso criado com sucesso!'}), 201


@app.route('/cursos/<int:id_curso>', methods=['PUT'])
@token_required
@roles_required('professor', 'parceiro', 'admin')
def editar_curso(current_user_id, current_user_role, id_curso):
    """Edição de curso — permitido para todos exceto alunos."""
    data = request.get_json()
    nome = data.get('nome')
    descricao = data.get('descricao')
    carga_horaria = data.get('carga_horaria')
    link_acesso = data.get('link_acesso')

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE cursos_extracurriculares
        SET nome = COALESCE(%s, nome),
            descricao = COALESCE(%s, descricao),
            carga_horaria = COALESCE(%s, carga_horaria),
            link_acesso = COALESCE(%s, link_acesso)
        WHERE id_cursos = %s
    """, (nome, descricao, carga_horaria, link_acesso, id_curso))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Curso atualizado com sucesso!'}), 200


@app.route('/cursos/<int:id_curso>', methods=['DELETE'])
@token_required
@roles_required('professor', 'parceiro', 'admin')
def deletar_curso(current_user_id, current_user_role, id_curso):
    """Exclusão de curso — permitido para todos exceto alunos."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cursos_extracurriculares WHERE id_cursos = %s", (id_curso,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Curso removido com sucesso!'}), 200


@app.route('/cursos/inscrever', methods=['POST'])
@token_required
@roles_required('aluno')
def inscrever_curso(current_user_id, current_user_role):
    """Inscrição em curso — apenas alunos podem."""
    data = request.get_json()
    id_curso = data.get('id_curso')

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Curso_Usuario (id_usuario, id_cursos, porcentagem_completada)
        VALUES (%s, %s, 0)
    """, (current_user_id, id_curso))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Inscrição realizada com sucesso!'}), 201


# ============================
# ROTAS PARA TEMAS DE TCC
# ============================

@app.route('/temas', methods=['GET'])
@token_required
def listar_temas(current_user_id, current_user_role):
    """Todos podem visualizar temas de TCC."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
    SELECT t.id_temas, t.nome AS titulo, t.area_conhecimento, t.data_criacao,
           u.nome_completo AS criado_por
    FROM tema_tcc t
    JOIN usuarios u ON t.criado_por = u.id_usuario
    ORDER BY t.data_criacao DESC
    """)

    temas = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({'temas': temas})


@app.route('/temas/criar', methods=['POST'])
@token_required
@roles_required('professor', 'parceiro', 'admin')
def criar_tema(current_user_id, current_user_role):
    """Professores, parceiros e admins podem propor temas de TCC."""
    data = request.get_json()
    nome = data.get('titulo')  # o front ainda envia "titulo", mas o campo no banco é "nome"
    print(data.get('titulo') )
    area_conhecimento = data.get('area_conhecimento')

    if not nome:
        return jsonify({'message': 'Título (nome) é obrigatório.'}), 400

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tema_tcc (nome, area_conhecimento, criado_por)
        VALUES (%s, %s, %s)
    """, (nome, area_conhecimento, current_user_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Tema de TCC criado com sucesso!'}), 201


@app.route('/temas/<int:id_tema>', methods=['DELETE'])
@token_required
@roles_required('professor', 'parceiro', 'admin')
def excluir_tema(current_user_id, current_user_role, id_tema):
    """Permite excluir tema de TCC (exceto alunos)."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tema_tcc WHERE id_tema = %s", (id_tema,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Tema de TCC removido com sucesso!'}), 200

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

@app.route('/perfil', methods=['POST'])
@token_required
@roles_required('aluno', 'professor')
def criar_ou_atualizar_perfil(current_user_id, current_user_role):
    data = request.get_json()
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO perfis_academicos (id_usuario, periodo_atual, ira_geral, interesses_principais, habilidades, objetivo_carreira)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE periodo_atual=%s, ira_geral=%s, interesses_principais=%s, habilidades=%s, objetivo_carreira=%s
    """, (current_user_id, data['periodo_atual'], data['ira_geral'], data['interesses_principais'],
          data['habilidades'], data['objetivo_carreira'],
          data['periodo_atual'], data['ira_geral'], data['interesses_principais'],
          data['habilidades'], data['objetivo_carreira']))
    conn.commit()
    return jsonify({'message': 'Perfil acadêmico salvo com sucesso!'})

@app.route('/perfil', methods=['GET'])
@token_required
def get_perfil(current_user_id, current_user_role):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM perfis_academicos WHERE id_usuario = %s", (current_user_id,))
    perfil = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({'perfil': perfil})


@app.route('/gemini/query', methods=['POST'])
@token_required
def gemini_query(current_user_id, current_user_role):
    data = request.get_json()
    prompt = data.get("prompt")
    if not prompt:
        return jsonify({"error": "Prompt é obrigatório"}), 400

    conn = None
    cursor = None

    try:
        # 🔹 Conecta e busca perfil acadêmico
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT periodo_atual, ira_geral, interesses_principais, habilidades, objetivo_carreira
            FROM perfis_academicos
            WHERE id_usuario = %s
        """, (current_user_id,))
        perfil = cursor.fetchone()

        contexto_extra = ""
        if perfil:
            contexto_extra = f"""
            O usuário está no período {perfil['periodo_atual']}, com IRA {perfil['ira_geral']}.
            Interesses: {perfil['interesses_principais']}.
            Habilidades: {perfil['habilidades']}.
            Objetivo de carreira: {perfil['objetivo_carreira']}.
            """

        # 🔹 Gera recomendação com Gemini
        prompt_final = f"""
        Usuário perguntou: "{prompt}"
        {contexto_extra}
        Gere uma resposta personalizada, útil e voltada à trajetória acadêmica e profissional do usuário.
        """
        response = cliente.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt_final
        )
        resposta_texto = response.text.strip()

        # 🔹 Salva recomendação no banco
        cursor.execute("""
            INSERT INTO recomendacoes (id_usuario, prompt, resposta)
            VALUES (%s, %s, %s)
        """, (current_user_id, prompt, resposta_texto))
        conn.commit()
        id_recomendacao = cursor.lastrowid

        return jsonify({
            "id_recomendacao": id_recomendacao,
            "prompt": prompt,
            "resposta": resposta_texto,
            "contexto_usado": bool(perfil),
            "message": "Recomendação gerada e salva com sucesso!"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/recomendacoes/<int:id_recomendacao>/avaliar', methods=['POST'])
@token_required
def avaliar_recomendacao(current_user_id, current_user_role, id_recomendacao):
    data = request.get_json()
    nota = data.get('nota')
    comentario = data.get('comentario', '')

    if nota is None or not (1 <= int(nota) <= 5):
        return jsonify({'message': 'A nota deve ser de 1 a 5.'}), 400

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO avaliacoes_recomendacao (id_recomendacao, id_usuario, nota, comentario)
        VALUES (%s, %s, %s, %s)
    """, (id_recomendacao, current_user_id, nota, comentario))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Avaliação registrada com sucesso!'}), 201

@app.route('/recomendacoes', methods=['GET'])
@token_required
def listar_recomendacoes(current_user_id, current_user_role):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id_recomendacao, prompt, resposta, data_geracao
        FROM recomendacoes
        WHERE id_usuario = %s
        ORDER BY data_geracao DESC
    """, (current_user_id,))
    recs = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({'recomendacoes': recs})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('email') or not data.get('senha'):
        return jsonify({'message': 'Email e senha são obrigatórios'}), 400

    email = data['email']
    senha = data['senha']

    conn = None
    cursor = None

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

        return jsonify({
            'token': token,
            'tipo_usuario': user['tipo_usuario']
        }), 200

    except mysql.connector.Error as err:
        print("Erro MySQL:", err)
        return jsonify({'message': 'Erro no banco de dados', 'error': str(err)}), 500

    except Exception as e:
        print("Erro inesperado:", e)
        return jsonify({'message': 'Erro interno no login', 'error': str(e)}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
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
