
CREATE DATABASE IF NOT EXISTS parameters;

CREATE TABLE IF NOT EXISTS parameters.parameter (
    name VARCHAR(511) NOT NULL,
    team VARCHAR(3),
    symbol VARCHAR(1023),
    units VARCHAR(255) CHARACTER SET utf8,
    is_derived SMALLINT,
    value VARCHAR(255)
);
    
CREATE TABLE IF NOT EXISTS parameters.dependency (
    name VARCHAR(511) NOT NULL,
    dependency VARCHAR(511)
);

CREATE TABLE IF NOT EXISTS parameters.expression (
    name VARCHAR(511) NOT NULL,
    expression VARCHAR(4095)
);

CREATE USER 'prm_editor'@'%' IDENTIFIED BY 'prm0';

GRANT SELECT, INSERT, UPDATE, DELETE ON parameters.* TO
    'prm_editor'@'%';
