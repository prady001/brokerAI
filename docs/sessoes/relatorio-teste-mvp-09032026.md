# Relatório de Testes MVP — BrokerAI
**Data:** 09/03/2026
**Ambiente:** Docker local (WSL2) + Twilio WhatsApp Sandbox
**Responsável:** Mateus

---

## 1. Objetivo

Validar os fluxos principais do MVP do BrokerAI em ambiente real — com mensagens WhatsApp reais, banco de dados PostgreSQL e agentes LangGraph ativos — antes de subir para produção.

---

## 2. Ambiente de Teste

| Componente | Configuração |
|---|---|
| API | FastAPI + Uvicorn, porta 8000, Docker |
| Banco | PostgreSQL 16, Docker |
| Cache | Redis 7, Docker |
| LLM | Google Gemini (fallback — Anthropic sem crédito) |
| WhatsApp | Twilio Sandbox (`+1 415 523 8886`) |
| Tunnel | Cloudflare Tunnel (`cloudflared`) — URL pública temporária |
| Webhook | `POST /webhook/whatsapp` — form-urlencoded Twilio |

---

## 3. Fluxos Testados

### 3.1 Cliente Desconhecido

**Cenário:** número não cadastrado envia mensagem.

**Passos:**
1. Número `5522981817697` entra no sandbox Twilio (`join let-stage`)
2. Envia qualquer mensagem para o sandbox

**Resultado:**
- ✅ Webhook recebido com sucesso (HTTP 200)
- ✅ Sistema identificou número não cadastrado
- ✅ Resposta enviada: *"Olá! Para que possamos ajudá-lo, por favor entre em contato com a corretora para cadastrar seus dados."*

---

### 3.2 Onboarding — Modo Pull (Cliente Inicia)

**Cenário:** cliente desconhecido pergunta como se cadastrar.

**Passos:**
1. `5522981817697` envia: *"como faço o cadastro?"*
2. Orquestrador detecta intenção `onboarding`
3. Bot coleta nome + CPF
4. Bot coleta dados da apólice
5. Bot confirma e persiste no banco

**Conversa registrada:**
```
[bot]    Olá! Sou o assistente da corretora. Para começarmos seu cadastro,
         preciso do seu nome completo e CPF, por favor.

[client] Gabriel Pradyumna Alencar Costa, Cpf: 13844432792

[bot]    Ótimo, Gabriel! Para sua apólice, qual é a seguradora, a descrição
         do item segurado, o número da apólice e a data de término?

[client] Bradesco Seguros, carro Honda Civic, apólice 123456, vence em 31/12/2026

[bot]    [confirmação dos dados]
```

**Resultado no banco:**
```
Cliente: Gabriel Pradyumna Alencar Costa | CPF: 184.469.327-92 | Tel: 5522981817697
Apólice: 123456 | Tipo: auto | Item: carro Honda Civic | Vence: 31/12/2026 | Status: active
```

- ✅ Detecção de intenção funcionou
- ✅ Coleta de dados em múltiplos turnos
- ✅ Cliente e apólice persistidos no PostgreSQL
- ✅ Estado de onboarding removido do Redis ao concluir

---

### 3.3 Sinistro Grave (Colisão)

**Cenário:** cliente cadastrado reporta batida de carro.

**Passos:**
1. `5522981817697` envia: *"bati meu carro"*
2. Agente de sinistros solicita número da apólice
3. Cliente informa `123456`
4. Sistema classifica severidade como **grave**
5. Escalona para o corretor

**Conversa registrada:**
```
[client] bati meu carro

[bot]    Sinto muito pelo ocorrido! Para te ajudar da melhor forma,
         por favor me informe a placa ou o número da apólice do seu veículo.

[client] 123456

[bot]    Entendido. Para o seu caso, um corretor especializado vai assumir
         o atendimento pessoalmente. Você será contatado em breve.
```

**Resultado no Redis:**
```
Status: escalated | Severity: grave | Escalated: true
```

- ✅ Intenção de sinistro detectada
- ✅ Severidade classificada corretamente como **grave**
- ✅ Conversa escalada para corretor (`5511921297395`)
- ✅ Estado mantido no Redis por 24h para follow-ups

---

### 3.4 Sinistro Simples (Vidro)

**Cenário:** cliente reporta vidro quebrado.

**Passos:**
1. Estado anterior limpo no Redis
2. `5522981817697` envia: *"o vidro do meu carro quebrou"*
3. Agente solicita número da apólice
4. Cliente informa `123456`
5. Sistema classifica severidade como **simples**
6. Protocolo gerado e acompanhamento iniciado

**Conversa registrada:**
```
[client] o vidro do meu carro quebrou

[bot]    Sinto muito pelo ocorrido! Para agilizar o atendimento, poderia
         me informar a placa ou o número do chassi do veículo, por favor?

[client] 123456

[bot]    Seu sinistro foi registrado! 🚗
         Protocolo: #73A1EF82
         Tipo: vidro | Apólice: carro Honda Civic
         Nossa equipe já foi notificada e vai acionar a seguradora.

[bot]    Ainda aguardando retorno da seguradora sobre seu sinistro.
         Assim que tivermos novidades, te avisamos aqui! ⏳
         Protocolo: #73A1EF82
```

**Resultado no Redis:**
```
Status: waiting_insurer | Severity: simple | Escalated: false
```

- ✅ Severidade classificada corretamente como **simples**
- ✅ **Não escalou** para corretor — bot gerencia diretamente
- ✅ Protocolo gerado automaticamente (`#73A1EF82`)
- ✅ Update de status enviado ao cliente

---

### 3.5 Renovação Automática (CRON)

**Cenário:** apólice vencendo em 7 dias — CRON dispara notificação.

**Passos:**
1. Apólice atualizada para vencer em `2026-03-16` (7 dias)
2. Endpoint `POST /scheduler/renewal-check` acionado manualmente
3. Sistema identifica apólice na janela de 7 dias
4. Mensagem de renovação enviada para `5522981817697`

**Resultado no banco:**
```
renewal: status=contacted | contact_count=1 | last_contact_at=2026-03-09 23:09
```

- ✅ CRON identificou apólice na janela de renovação
- ✅ Mensagem enviada ao cliente via WhatsApp
- ✅ Registro de contato salvo no banco
- ✅ Próximo contato agendado automaticamente

---

## 4. Resumo dos Resultados

| Fluxo | Resultado | Observações |
|---|---|---|
| Cliente desconhecido | ✅ OK | Resposta padrão enviada |
| Onboarding pull | ✅ OK | Cadastro completo no banco |
| Sinistro grave | ✅ OK | Escalonado para corretor |
| Sinistro simples | ✅ OK | Bot acompanha com protocolo |
| Renovação (CRON) | ✅ OK | Notificação enviada |

**Bugs encontrados e corrigidos durante os testes:**
1. `renewal_service.py` — `expiry_dt` com `tzinfo=UTC` causava erro no PostgreSQL → removido `tzinfo`
2. Twilio — container Docker carregando `.env` antigo → solução: `--force-recreate`
3. Validação de assinatura Twilio — URL do tunnel difere de `request.url` → pular em `development`

---

## 5. Caminho para Produção

### 5.1 O que já está pronto

Todo o código do MVP está implementado e validado. Não é necessário nenhuma mudança de código para ir a produção — apenas configurações de infraestrutura.

### 5.2 Passo a Passo para Produção

#### Etapa 1 — Servidor (VPS)

Escolha um dos provedores:

| Provedor | Plano recomendado | Custo |
|---|---|---|
| **GCP (Google Cloud)** | e2-small (2 vCPU, 2GB RAM) | ~$15/mês |
| **AWS** | t3.small | ~$15/mês |
| **DigitalOcean** | Droplet 2GB | ~$12/mês |
| **Hetzner** | CX21 (2 vCPU, 4GB) | ~€4/mês ✅ melhor custo |

Requisitos mínimos: **2 vCPU, 2GB RAM, 20GB disco**, Ubuntu 22.04, Docker instalado.

#### Etapa 2 — Domínio e HTTPS

1. Registrar domínio (ex: `app.brokerai.com.br`)
2. Configurar DNS apontando para o IP do servidor
3. Certificado SSL via Let's Encrypt (gratuito) com Nginx como reverse proxy

#### Etapa 3 — WhatsApp Twilio (saída do sandbox)

1. Acessar **Twilio Console → WhatsApp → Senders**
2. Solicitar número WhatsApp Business (aprovação Meta — 1 a 3 dias úteis)
3. Atualizar `.env` de produção:
   ```
   TWILIO_WHATSAPP_FROM=whatsapp:+55XXXXXXXXXXX
   ```
4. Configurar webhook no Twilio apontando para `https://app.brokerai.com.br/webhook/whatsapp`

#### Etapa 4 — Variáveis de Ambiente de Produção

```env
ENVIRONMENT=production
LLM_PROVIDER=anthropic          # ou google
ANTHROPIC_API_KEY=sk-ant-...    # recarregar ~$5
DATABASE_URL=postgresql+asyncpg://usuario:senha@localhost:5432/brokerai
REDIS_URL=redis://localhost:6379/0
TWILIO_ACCOUNT_SID=ACxxxx
TWILIO_AUTH_TOKEN=xxxx
TWILIO_WHATSAPP_FROM=whatsapp:+55XXXXXXXXXXX
BROKER_NOTIFICATION_PHONE=5511921297395
INTERNAL_API_TOKEN=<token seguro gerado>
```

#### Etapa 5 — Deploy

```bash
# No servidor
git clone https://github.com/seu-usuario/brokerai.git
cd brokerai
cp .env.example .env
# preencher .env com valores de produção
docker compose up -d
docker compose exec api alembic upgrade head
```

#### Etapa 6 — CRON de Renovação

O scheduler já está configurado no `docker-compose.yml`. Em produção, verificar se o serviço `scheduler` está rodando:

```bash
docker compose ps scheduler
```

---

### 5.3 Custos Mensais Estimados (produção — 1 corretora piloto)

| Item | Custo |
|---|---|
| VPS Hetzner CX21 | ~R$ 25/mês |
| Twilio WhatsApp (~200 conversas) | ~R$ 10/mês |
| Google Gemini API | ~R$ 5-15/mês |
| Domínio (.com.br) | ~R$ 4/mês |
| **Total** | **~R$ 45-55/mês** |

Com **Anthropic Claude** no lugar do Gemini: acrescentar ~R$ 20-40/mês dependendo do volume.

---

### 5.4 Checklist Final antes do Go-Live

- [ ] VPS provisionado e Docker instalado
- [ ] Domínio configurado com HTTPS
- [ ] Número WhatsApp aprovado no Twilio
- [ ] `.env` de produção preenchido com todos os valores reais
- [ ] `ENVIRONMENT=production` — ativa validação de assinatura Twilio
- [ ] `INTERNAL_API_TOKEN` definido — protege rotas `/admin` e `/scheduler`
- [ ] Migrations aplicadas (`alembic upgrade head`)
- [ ] Webhook configurado no Twilio apontando para domínio de produção
- [ ] Teste de smoke: enviar mensagem real e verificar resposta
- [ ] Backup automático do PostgreSQL configurado
