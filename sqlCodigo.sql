-- ENUMS
CREATE TYPE tipo_usuario_enum AS ENUM ('aluno', 'professor', 'admin', 'parceiro');
CREATE TYPE tipo_parceiro_enum AS ENUM ('faculdade', 'empresa');
CREATE TYPE situacao_enum AS ENUM ('aprovado', 'reprovado', 'cursando', 'trancado');
CREATE TYPE tipo_material_enum AS ENUM ('pdf', 'ppt', 'doc', 'outro');
CREATE TYPE tipo_endereco_enum AS ENUM ('residencial', 'comercial', 'outro');
CREATE TYPE tipo_preferencia_enum AS ENUM ('curso_extracurricular', 'tema_tcc', 'carreira');

-- Função padrão para atualizar data_atualizacao
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.data_atualizacao = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- usuarios
CREATE TABLE usuarios (
    id_usuario SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    nome_completo VARCHAR(255) NOT NULL,
    data_nascimento DATE,
    genero VARCHAR(50),
    curso_atual VARCHAR(100) NOT NULL,
    data_criacao TIMESTAMP DEFAULT NOW(),
    data_atualizacao TIMESTAMP DEFAULT NOW(),
    tipo_usuario tipo_usuario_enum NOT NULL,
    ativo BOOLEAN DEFAULT TRUE
);
ALTER TABLE usuarios ADD COLUMN auth_id UUID;

CREATE TRIGGER trg_update_usuarios
BEFORE UPDATE ON usuarios
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- dados_professor
CREATE TABLE dados_professor (
    id_professor SERIAL PRIMARY KEY,
    id_usuario INT NOT NULL UNIQUE REFERENCES usuarios(id_usuario),
    formacao VARCHAR(255),
    area_atuacao VARCHAR(255),
    tempo_experiencia INT
);

-- parceiros
CREATE TABLE parceiros (
    id_parceiro SERIAL PRIMARY KEY,
    id_usuario INT NOT NULL UNIQUE REFERENCES usuarios(id_usuario),
    tipo_parceiro tipo_parceiro_enum NOT NULL,
    nome_fantasia VARCHAR(255),
    razao_social VARCHAR(255),
    cnpj VARCHAR(18),
    telefone VARCHAR(20),
    email VARCHAR(255),
    site VARCHAR(255)
);

-- perfis_academicos
CREATE TABLE perfis_academicos (
    id_perfil_academico SERIAL PRIMARY KEY,
    id_usuario INT NOT NULL UNIQUE REFERENCES usuarios(id_usuario),
    periodo_atual INT,
    ira_geral DECIMAL(4,2),
    interesses_principais TEXT,
    habilidades TEXT,
    objetivo_carreira TEXT,
    data_atualizacao TIMESTAMP DEFAULT NOW()
);

CREATE TRIGGER trg_update_perfis_academicos
BEFORE UPDATE ON perfis_academicos
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- historico_disciplinas
CREATE TABLE historico_disciplinas (
    id_historico_disc SERIAL PRIMARY KEY,
    id_usuario INT NOT NULL REFERENCES usuarios(id_usuario),
    nome_disciplina VARCHAR(150) NOT NULL,
    codigo_disciplina VARCHAR(20),
    periodo_cursado INT NOT NULL,
    nota_final DECIMAL(4,2) NOT NULL,
    situacao situacao_enum NOT NULL,
    data_registro TIMESTAMP DEFAULT NOW()
);
-- enderecos
CREATE TABLE enderecos (
    id_endereco SERIAL PRIMARY KEY,
    id_usuario INT NOT NULL REFERENCES usuarios(id_usuario),
    cep VARCHAR(9) NOT NULL,
    logradouro VARCHAR(255) NOT NULL,
    numero VARCHAR(10) NOT NULL,
    complemento VARCHAR(100),
    bairro VARCHAR(100) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    estado VARCHAR(2) NOT NULL,
    pais VARCHAR(100) DEFAULT 'Brasil',
    tipo_endereco tipo_endereco_enum DEFAULT 'residencial',
    data_criacao TIMESTAMP DEFAULT NOW(),
    data_atualizacao TIMESTAMP DEFAULT NOW()
);

CREATE TRIGGER trg_update_enderecos
BEFORE UPDATE ON enderecos
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- preferencias_recomendacao
CREATE TABLE preferencias_recomendacao (
    id_preferencia SERIAL PRIMARY KEY,
    id_usuario INT NOT NULL UNIQUE REFERENCES usuarios(id_usuario),
    tipo_preferencia tipo_preferencia_enum NOT NULL,
    preferencias_json JSONB,
    data_atualizacao TIMESTAMP DEFAULT NOW()
);

CREATE TRIGGER trg_update_preferencias
BEFORE UPDATE ON preferencias_recomendacao
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- foruns
CREATE TABLE foruns (
    id_forum SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    criado_por INT REFERENCES usuarios(id_usuario),
    data_criacao TIMESTAMP DEFAULT NOW()
);

-- publicacoes_forum
CREATE TABLE publicacoes_forum (
    id_publicacao SERIAL PRIMARY KEY,
    id_usuario INT NOT NULL REFERENCES usuarios(id_usuario),
    titulo VARCHAR(255) NOT NULL,
    conteudo TEXT NOT NULL,
    categoria VARCHAR(100),
    data_criacao TIMESTAMP DEFAULT NOW(),
    data_atualizacao TIMESTAMP DEFAULT NOW(),
    id_forum INT NOT NULL REFERENCES foruns(id_forum) ON DELETE CASCADE
);

CREATE TRIGGER trg_update_publicacoes
BEFORE UPDATE ON publicacoes_forum
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- cursos_extracurriculares
CREATE TABLE cursos_extracurriculares (
    id_cursos SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT NOT NULL,
    carga_horaria INT DEFAULT 0,
    link_acesso VARCHAR(255),
    criado_por INT REFERENCES usuarios(id_usuario)
);

-- tema_tcc
CREATE TABLE tema_tcc (
    id_tema SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT NOT NULL,
    area_conhecimento VARCHAR(100),
    data_criacao TIMESTAMP DEFAULT NOW(),
    criado_por INT REFERENCES usuarios(id_usuario)
);

-- tema_tcc_cursos
CREATE TABLE tema_tcc_cursos (
    id_relacao SERIAL PRIMARY KEY,
    id_tema INT NOT NULL REFERENCES tema_tcc(id_tema) ON DELETE CASCADE,
    id_cursos INT NOT NULL REFERENCES cursos_extracurriculares(id_cursos)
);

-- materiais
CREATE TABLE materiais (
    id_material SERIAL PRIMARY PRIMARY KEY,
    id_usuario INT NOT NULL REFERENCES usuarios(id_usuario),
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT,
    tipo_material tipo_material_enum DEFAULT 'outro',
    caminho_arquivo VARCHAR(500) NOT NULL,
    data_upload TIMESTAMP DEFAULT NOW(),
    tipo VARCHAR(50) DEFAULT 'outro'
);

-- recomendacoes
CREATE TABLE recomendacoes (
    id_recomendacao SERIAL PRIMARY KEY,
    id_usuario INT NOT NULL REFERENCES usuarios(id_usuario),
    prompt TEXT NOT NULL,
    resposta TEXT NOT NULL,
    data_geracao TIMESTAMP DEFAULT NOW()
);

-- avaliacoes_recomendacao
CREATE TABLE avaliacoes_recomendacao (
    id_avaliacao SERIAL PRIMARY KEY,
    id_recomendacao INT NOT NULL REFERENCES recomendacoes(id_recomendacao),
    id_usuario INT NOT NULL REFERENCES usuarios(id_usuario),
    nota SMALLINT CHECK (nota BETWEEN 1 AND 5),
    comentario TEXT,
    data_avaliacao TIMESTAMP DEFAULT NOW()
);
