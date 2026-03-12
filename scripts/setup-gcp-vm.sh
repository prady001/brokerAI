#!/bin/bash
# setup-gcp-vm.sh
# Rodar este script na VM do GCP após o primeiro acesso SSH
# Instala Docker, copia config e sobe a Evolution API

set -e

echo "=== [1/4] Instalando Docker ==="
sudo apt-get update -qq
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -qq
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER

echo "=== [2/4] Obtendo IP público ==="
VM_IP=$(curl -s ifconfig.me)
echo "IP público da VM: $VM_IP"

echo "=== [3/4] Criando docker-compose.yml ==="
mkdir -p ~/brokerai
cat > ~/brokerai/docker-compose.yml << COMPOSE
version: "3.8"

services:
  postgres:
    image: postgres:16
    restart: always
    environment:
      POSTGRES_DB: evolution
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  evolution-api:
    image: atendai/evolution-api:latest
    restart: always
    ports:
      - "8080:8080"
    environment:
      SERVER_URL: http://${VM_IP}:8080
      AUTHENTICATION_TYPE: apikey
      AUTHENTICATION_API_KEY: brokerai-secret-2026
      AUTHENTICATION_EXPOSE_IN_FETCH_INSTANCES: "true"
      DATABASE_ENABLED: "true"
      DATABASE_PROVIDER: postgresql
      DATABASE_CONNECTION_URI: postgresql://postgres:postgres@postgres:5432/evolution
      DATABASE_CONNECTION_CLIENT_NAME: evolution_api
      DATABASE_SAVE_DATA_INSTANCE: "true"
      DATABASE_SAVE_DATA_NEW_MESSAGE: "true"
      DATABASE_SAVE_MESSAGE_UPDATE: "true"
      DATABASE_SAVE_DATA_CONTACTS: "true"
      DATABASE_SAVE_DATA_CHATS: "true"
      DATABASE_SAVE_DATA_HISTORIC: "true"
      CACHE_REDIS_ENABLED: "true"
      CACHE_REDIS_URI: redis://redis:6379/0
      CACHE_REDIS_PREFIX_KEY: evolution
      CACHE_REDIS_SAVE_INSTANCES: "true"
      CACHE_LOCAL_ENABLED: "false"
      WEBHOOK_GLOBAL_ENABLED: "false"
      DEL_INSTANCE: "false"
      LANGUAGE: pt-BR
      LOG_LEVEL: ERROR
      LOG_COLOR: "true"
      LOG_BAILEYS: warn
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - evolution_instances:/evolution/instances

volumes:
  postgres_data:
  redis_data:
  evolution_instances:
COMPOSE

echo "=== [4/4] Subindo Evolution API ==="
cd ~/brokerai
sudo docker compose up -d

echo ""
echo "=== PRONTO ==="
echo "Manager: http://${VM_IP}:8080/manager"
echo "API Key: brokerai-secret-2026"
echo ""
echo "Aguarde ~30 segundos e acesse o manager no browser para criar e parear a instância."
