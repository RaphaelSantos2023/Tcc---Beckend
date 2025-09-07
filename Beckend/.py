from flask import Flask, request, jsonify
import mysql.connector
from sentence_transformers import SentenceTransformer, util

# Modelo de embeddings (pré-treinado para semântica)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Conexão MySQL
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'tcc_bd'
}

app = Flask(__name__)

def get_dados_usuario(id_usuario):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Busca perfil acadêmico + preferências
    cursor.execute("""
        SELECT p.interesses_principais, p.habilidades, pr.tipo_preferencia, pr.preferencias_json
        FROM perfis_academicos p
        LEFT JOIN preferencias_recomendacao pr ON p.id_usuario = pr.id_usuario
        WHERE p.id_usuario = %s
    """, (id_usuario,))
    dados = cursor.fetchall()

    cursor.close()
    conn.close()
    return dados

def get_temas_cursos():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Pega cursos e temas
    cursor.execute("SELECT id_cursos, nome, descricao FROM cursos_extracurriculares")
    cursos = cursor.fetchall()

    cursor.execute("SELECT id_temas, nome FROM Tema_tcc")
    temas = cursor.fetchall()

    cursor.close()
    conn.close()
    return cursos, temas

def recomendar(id_usuario, top_n=3):
    dados_usuario = get_dados_usuario(id_usuario)
    cursos, temas = get_temas_cursos()

    if not dados_usuario:
        return {"erro": "Usuário não encontrado"}

    # Junta interesses + habilidades como "perfil de texto"
    perfil_texto = " ".join([
        (d["interesses_principais"] or "") + " " + 
        (d["habilidades"] or "") + " " + 
        (d.get("preferencias_json", "") or "")
        for d in dados_usuario
    ])


    # Embedding do usuário
    emb_usuario = model.encode(perfil_texto, convert_to_tensor=True)

    # Calcular similaridade para cursos
    cursos_scores = []
    for c in cursos:
        texto_curso = f"{c['nome']} {c['descricao']}"
        emb_curso = model.encode(texto_curso, convert_to_tensor=True)
        score = util.cos_sim(emb_usuario, emb_curso).item()
        cursos_scores.append((c['id_cursos'], c['nome'], score))

    cursos_scores.sort(key=lambda x: x[2], reverse=True)

    # Calcular similaridade para temas
    temas_scores = []
    for t in temas:
        emb_tema = model.encode(t['nome'], convert_to_tensor=True)
        score = util.cos_sim(emb_usuario, emb_tema).item()
        temas_scores.append((t['id_temas'], t['nome'], score))

    temas_scores.sort(key=lambda x: x[2], reverse=True)

    return {
        "recomendacoes_cursos": cursos_scores[:top_n],
        "recomendacoes_temas": temas_scores[:top_n]
    }

@app.route("/recomendar/<int:id_usuario>", methods=["GET"])
def api_recomendar(id_usuario):
    resultado = recomendar(id_usuario)
    return jsonify(resultado)

if __name__ == "__main__":
    app.run(debug=True)
