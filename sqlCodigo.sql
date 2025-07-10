-- Criação do banco de dados
CREATE DATABASE tcc_bd;
USE tcc_bd;

-- Tabela: usuarios
CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    nome_completo VARCHAR(255) NOT NULL,
    data_nascimento DATE,
    genero VARCHAR(50),
    curso_atual VARCHAR(100) NOT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    tipo_usuario ENUM('aluno', 'professor', 'admin') NOT NULL,
    ativo BOOLEAN DEFAULT TRUE
);

-- Tabela: perfis_academicos
CREATE TABLE perfis_academicos (
    id_perfil_academico INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL UNIQUE,
    periodo_atual INT,
    ira_geral DECIMAL(4,2),
    interesses_principais TEXT,
    habilidades TEXT,
    objetivo_carreira TEXT,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);

-- Tabela: historico_disciplinas
CREATE TABLE historico_disciplinas (
    id_historico_disc INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    nome_disciplina VARCHAR(150) NOT NULL,
    codigo_disciplina VARCHAR(20),
    periodo_cursado INT NOT NULL,
    nota_final DECIMAL(4,2) NOT NULL,
    situacao ENUM('aprovado', 'reprovado', 'cursando', 'trancado') NOT NULL,
    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);

-- Tabela: preferencias_recomendacao
CREATE TABLE preferencias_recomendacao (
    id_preferencia INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL UNIQUE,
    tipo_preferencia ENUM('curso_extracurricular', 'tema_tcc', 'carreira') NOT NULL,
    preferencias_json JSON,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);
