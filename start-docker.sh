#!/bin/bash

# ================================
# Aluvi - Script de Inicialização Docker
# ================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função de log
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Verificar pré-requisitos
check_prerequisites() {
    log "Verificando pré-requisitos..."

    # Docker
    if ! command -v docker &> /dev/null; then
        error "Docker não está instalado. Instale o Docker primeiro."
        exit 1
    fi

    # Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose não está instalado."
        exit 1
    fi

    # Verificar versão do Docker
    DOCKER_VERSION=$(docker --version | sed 's/Docker version //' | cut -d. -f1)
    if [ "$DOCKER_VERSION" -lt 20 ]; then
        warn "Docker versão $DOCKER_VERSION detectada. Recomendado: 20.10+"
    fi

    log "Pré-requisitos OK!"
}

# Criar arquivo .env se não existir
setup_environment() {
    if [ ! -f .env ]; then
        log "Criando arquivo .env..."
        cp .env.example .env
        warn "Arquivo .env criado. Configure as variáveis de ambiente se necessário."
        warn "IMPORTANTE: Mude SECRET_KEY e senhas em produção!"
    else
        log "Arquivo .env já existe."
    fi
}

# Verificar se portas estão livres
check_ports() {
    log "Verificando portas..."

    local ports=(80 8000 5432 6379 9090 3000 3100)
    local occupied_ports=()

    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            occupied_ports+=($port)
        fi
    done

    if [ ${#occupied_ports[@]} -ne 0 ]; then
        warn "Portas ocupadas: ${occupied_ports[*]}"
        warn "Se houver conflitos, edite docker-compose.yml para mudar as portas."
        read -p "Continuar mesmo assim? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log "Todas as portas estão livres."
    fi
}

# Build e start dos serviços
start_services() {
    local build_flag=""
    local detach_flag="-d"

    # Verificar se devemos fazer build
    if [ "$1" = "--build" ] || [ "$1" = "-b" ]; then
        build_flag="--build"
        log "Fazendo build dos serviços..."
    fi

    # Verificar se deve rodar em foreground
    if [ "$1" = "--foreground" ] || [ "$1" = "-f" ]; then
        detach_flag=""
        log "Iniciando em foreground (pressione Ctrl+C para parar)..."
    fi

    # Comando docker-compose
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    else
        DOCKER_COMPOSE_CMD="docker compose"
    fi

    log "Iniciando serviços com $DOCKER_COMPOSE_CMD..."
    $DOCKER_COMPOSE_CMD up $build_flag $detach_flag
}

# Aguardar serviços ficarem saudáveis
wait_for_services() {
    log "Aguardando serviços ficarem prontos..."

    local services=("db" "redis" "backend")
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        local all_healthy=true

        for service in "${services[@]}"; do
            if ! $DOCKER_COMPOSE_CMD ps $service | grep -q "Up"; then
                all_healthy=false
                break
            fi
        done

        if $all_healthy; then
            log "Todos os serviços estão rodando!"
            return 0
        fi

        info "Tentativa $attempt/$max_attempts - Aguardando serviços..."
        sleep 10
        ((attempt++))
    done

    warn "Timeout aguardando serviços. Verifique os logs:"
    warn "docker-compose logs"
    return 1
}

# Mostrar informações de acesso
show_access_info() {
    log "🎉 Serviços iniciados com sucesso!"
    echo
    info "📱 Acesse a aplicação:"
    echo "   Frontend (SPA):     http://localhost"
    echo "   API Docs:           http://localhost/api/docs"
    echo "   Health Check:       http://localhost/health"
    echo
    info "📊 Monitoramento:"
    echo "   Grafana:            http://localhost:3000 (admin/admin)"
    echo "   Prometheus:         http://localhost:9090"
    echo "   Loki (Logs):        http://localhost:3100"
    echo
    info "🗄️ Banco de dados:"
    echo "   PostgreSQL:         localhost:5432"
    echo "   Redis:              localhost:6379"
    echo
    info "🔧 Comandos úteis:"
    echo "   Ver logs:           docker-compose logs -f [serviço]"
    echo "   Parar tudo:         docker-compose down"
    echo "   Reset banco:        docker-compose down -v && $0"
    echo
    warn "⚠️  IMPORTANTE: Configure senhas seguras em produção!"
    warn "⚠️  Primeiro acesso pode demorar devido ao build inicial."
}

# Função principal
main() {
    echo "🚀 Aluvi - Sistema de Agendamentos"
    echo "=================================="
    echo

    # Verificar argumentos
    case "${1:-}" in
        "stop")
            log "Parando serviços..."
            $DOCKER_COMPOSE_CMD down
            log "Serviços parados."
            exit 0
            ;;
        "restart")
            log "Reiniciando serviços..."
            $DOCKER_COMPOSE_CMD restart
            log "Serviços reiniciados."
            exit 0
            ;;
        "logs")
            $DOCKER_COMPOSE_CMD logs -f "${2:-}"
            exit 0
            ;;
        "status")
            $DOCKER_COMPOSE_CMD ps
            exit 0
            ;;
        "clean")
            warn "Isso irá remover TODOS os containers, volumes e imagens!"
            read -p "Tem certeza? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                log "Limpando tudo..."
                $DOCKER_COMPOSE_CMD down -v --rmi all
                docker system prune -f
                log "Limpeza concluída."
            fi
            exit 0
            ;;
        "help"|"-h"|"--help")
            echo "Uso: $0 [opção]"
            echo
            echo "Opções:"
            echo "  (vazio)     Iniciar serviços em background"
            echo "  --build     Fazer build antes de iniciar"
            echo "  --foreground  Iniciar em foreground"
            echo "  stop         Parar serviços"
            echo "  restart      Reiniciar serviços"
            echo "  logs         Ver logs (opcional: serviço específico)"
            echo "  status       Ver status dos serviços"
            echo "  clean        Limpar tudo (CUIDADO!)"
            echo "  help         Mostrar esta ajuda"
            echo
            exit 0
            ;;
    esac

    # Inicialização normal
    check_prerequisites
    setup_environment
    check_ports

    # Iniciar serviços
    if [ "$1" = "--build" ] || [ "$1" = "-b" ]; then
        start_services --build
    elif [ "$1" = "--foreground" ] || [ "$1" = "-f" ]; then
        start_services --foreground
    else
        start_services
        wait_for_services
        show_access_info
    fi
}

# Executar função principal
main "$@"