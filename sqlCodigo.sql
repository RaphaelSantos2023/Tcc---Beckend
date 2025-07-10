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
    tipo_usuario ENUM('aluno', 'professor', 'admin', 'parceiro') NOT NULL,
    ativo BOOLEAN DEFAULT TRUE
);

CREATE TABLE dados_professor (
    id_professor INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL UNIQUE,
    formacao VARCHAR(255),
    area_atuacao VARCHAR(255),
    tempo_experiencia INT,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);

CREATE TABLE parceiros (
    id_parceiro INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL UNIQUE,
    tipo_parceiro ENUM('faculdade', 'empresa') NOT NULL,
    nome_fantasia VARCHAR(255),
    razao_social VARCHAR(255),
    cnpj VARCHAR(18),
    telefone VARCHAR(20),
    email VARCHAR(255),
    site VARCHAR(255),
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
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

CREATE TABLE enderecos (
    id_endereco INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    cep VARCHAR(9) NOT NULL,
    logradouro VARCHAR(255) NOT NULL,
    numero VARCHAR(10) NOT NULL,
    complemento VARCHAR(100),
    bairro VARCHAR(100) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    estado VARCHAR(2) NOT NULL,
    pais VARCHAR(100) DEFAULT 'Brasil',
    tipo_endereco ENUM('residencial', 'comercial', 'outro') DEFAULT 'residencial',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
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
