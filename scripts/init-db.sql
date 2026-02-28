-- Cria o banco de dados separado para a Evolution API (WhatsApp).
-- Executado automaticamente pelo postgres na primeira inicialização do container.
-- O banco principal (insurance_agents) é criado pela variável POSTGRES_DB.

SELECT 'CREATE DATABASE evolution'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'evolution'
)\gexec
