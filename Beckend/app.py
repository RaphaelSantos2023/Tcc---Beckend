from flask import Flask, request, jsonify
import mysql.connector
from passlib.hash import bcrypt
import jwt
import datetime
from functools import wraps
from flask_cors import CORS
import os
from google import genai
cliente = genai.Client(api_key="Chave_api")

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'sua_chave_super_secreta'  # Troque para algo seguro

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'tcc_bd'
}



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

        # Passa id e role para a função protegida
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

        cursor.execute("SELECT id_usuario, senha_hash FROM usuarios WHERE email = %s AND ativo = TRUE", (email,))
        user = cursor.fetchone()

        if not user or not bcrypt.verify(senha, user['senha_hash']):
            return jsonify({'message': 'Usuário ou senha incorretos'}), 401

        token = jwt.encode({
            'id_usuario': user['id_usuario'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        }, app.config['SECRET_KEY'], algorithm="HS256")

        return jsonify({'token': token})

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

@app.route('/forum/publicar', methods=['POST'])
@token_required
@roles_required('aluno', 'professor', 'admin')
def publicar_post(current_user_id, current_user_role):
    data = request.get_json()
    titulo = data.get('titulo')
    conteudo = data.get('conteudo')
    categoria = data.get('categoria')

    if not titulo or not conteudo:
        return jsonify({'message': 'Título e conteúdo são obrigatórios.'}), 400

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO publicacoes_forum (id_usuario, titulo, conteudo, categoria)
            VALUES (%s, %s, %s, %s)
        """, (current_user_id, titulo, conteudo, categoria))
        conn.commit()

        return jsonify({'message': 'Publicação criada com sucesso!'}), 201

    except mysql.connector.Error as err:
        return jsonify({'message': 'Erro ao criar publicação.', 'error': str(err)}), 500

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/forum/publicacoes', methods=['GET'])
@token_required
def listar_publicacoes(current_user_id, current_user_role):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT p.id_publicacao, p.titulo, p.conteudo, p.categoria, p.data_criacao,
                   u.nome_completo AS autor
            FROM publicacoes_forum p
            JOIN usuarios u ON p.id_usuario = u.id_usuario
            ORDER BY p.data_criacao DESC
        """)
        posts = cursor.fetchall()
        return jsonify({'publicacoes': posts})

    except mysql.connector.Error as err:
        return jsonify({'message': 'Erro ao buscar publicações.', 'error': str(err)}), 500

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/forum/publicacoes/<int:id_publicacao>/responder', methods=['POST'])
@token_required
def responder_publicacao(current_user_id, current_user_role, id_publicacao):
    data = request.get_json()
    conteudo = data.get('conteudo')

    if not conteudo:
        return jsonify({'message': 'Conteúdo da resposta é obrigatório.'}), 400

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO respostas_forum (id_publicacao, id_usuario, conteudo)
            VALUES (%s, %s, %s)
        """, (id_publicacao, current_user_id, conteudo))
        conn.commit()

        return jsonify({'message': 'Resposta publicada com sucesso.'}), 201

    except mysql.connector.Error as err:
        return jsonify({'message': 'Erro ao salvar resposta.', 'error': str(err)}), 500

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/forum/publicacoes/<int:id_publicacao>', methods=['GET'])
@token_required
def detalhes_publicacao(current_user_id, current_user_role, id_publicacao):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Obter a publicação
        cursor.execute("""
            SELECT p.id_publicacao, p.titulo, p.conteudo, p.categoria, p.data_criacao,
                   u.nome_completo AS autor
            FROM publicacoes_forum p
            JOIN usuarios u ON p.id_usuario = u.id_usuario
            WHERE p.id_publicacao = %s
        """, (id_publicacao,))
        publicacao = cursor.fetchone()

        if not publicacao:
            return jsonify({'message': 'Publicação não encontrada.'}), 404

        # Obter as respostas
        cursor.execute("""
            SELECT r.id_resposta, r.conteudo, r.data_criacao, u.nome_completo AS autor
            FROM respostas_forum r
            JOIN usuarios u ON r.id_usuario = u.id_usuario
            WHERE r.id_publicacao = %s
            ORDER BY r.data_criacao ASC
        """, (id_publicacao,))
        respostas = cursor.fetchall()

        publicacao['respostas'] = respostas
        return jsonify({'publicacao': publicacao})

    except mysql.connector.Error as err:
        return jsonify({'message': 'Erro ao buscar detalhes da publicação.', 'error': str(err)}), 500

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

if __name__ == '__main__':
    app.run(debug=True)
