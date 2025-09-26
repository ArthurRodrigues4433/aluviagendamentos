-- Inicialização do banco de dados Aluvi
-- Executado automaticamente no primeiro startup do container PostgreSQL

-- Criar extensão para UUID (se necessário)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Configurações de performance (comentadas - pg_stat_statements não disponível na imagem Alpine)
-- ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
-- ALTER SYSTEM SET pg_stat_statements.max = 10000;
-- ALTER SYSTEM SET pg_stat_statements.track = 'all';

-- Configurações de logging
ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';
ALTER SYSTEM SET log_statement = 'ddl';
ALTER SYSTEM SET log_duration = on;

-- Configurações de conexão
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Criar usuário dedicado para a aplicação (já criado via environment)
-- GRANT ALL PRIVILEGES ON DATABASE aluvi TO aluvi_user;

-- Configurar timezone
SET timezone = 'America/Sao_Paulo';

-- Criar função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Criar função para soft delete
CREATE OR REPLACE FUNCTION soft_delete_record()
RETURNS TRIGGER AS $$
BEGIN
    NEW.deleted_at = CURRENT_TIMESTAMP;
    NEW.is_active = false;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Comentários no banco
COMMENT ON DATABASE aluvi IS 'Sistema de Agendamentos Aluvi - Produção';
COMMENT ON SCHEMA public IS 'Schema padrão do sistema Aluvi';

-- Criar índices otimizados (serão criados automaticamente pelo SQLAlchemy)
-- Os índices serão criados durante a inicialização da aplicação

-- Configurar permissões básicas
GRANT USAGE ON SCHEMA public TO aluvi_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aluvi_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO aluvi_user;

-- Configuração para futuras tabelas
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO aluvi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO aluvi_user;

-- Log da inicialização
DO $$
BEGIN
    RAISE NOTICE 'Banco de dados Aluvi inicializado com sucesso em %', CURRENT_TIMESTAMP;
END $$;