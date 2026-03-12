# Brainstorm: Painel do Gestor

**Data:** 2026-03-10
**Status:** Rascunho

---

## O que estamos construindo

Um painel web para o corretor visualizar e operar sua base de clientes e apólices. Acesso via navegador, usuário único (o corretor), com login obrigatório.

O painel não substitui os agentes — é a interface humana para monitorar o que os agentes estão fazendo e consultar a base de dados.

---

## Por que essa abordagem

O corretor hoje opera às cegas: os agentes recebem mensagens, cadastram clientes e gerenciam renovações — mas não existe nenhuma tela para ver o resultado disso. O painel fecha esse gap sem mudar nada na lógica dos agentes.

**Stack escolhida: React/Next.js (frontend) + FastAPI (backend JSON)**

- Frontend desacoplado: pode evoluir independente da API
- Next.js: SSR nativo, roteamento simples, fácil de hospedar (Vercel ou Docker)
- A API já tem rotas `/admin` parcialmente implementadas — só expandir

---

## O que é essencial (MVP do painel)

### 1. Dashboard (tela inicial)
- Contadores: total de clientes, apólices ativas, renovações pendentes, sinistros abertos
- Apólices vencendo nos próximos 30/60/90 dias (lista com alerta visual)
- Onboardings em andamento (estado no Redis)
- Conversas ativas no WhatsApp

### 2. Base de Clientes
- Tabela com busca por nome, CPF ou telefone
- Paginação (já suportada pela rota `/admin/clients`)
- Clicar no cliente abre o detalhe

### 3. Detalhe do Cliente
- Dados cadastrais (nome, CPF, telefone, email)
- Apólices do cliente (número, seguradora, tipo, vigência, status)
- Histórico de sinistros
- Histórico de renovações e intenção declarada (confirmou, recusou, sem resposta)

### 4. Status dos Agentes
- Onboardings em andamento (chaves Redis `onboarding_conversation:*`)
- Conversas de sinistro ativas (chaves Redis `claim_conversation:*`)

---

## O que está faltando no backend

A pesquisa identificou lacunas que precisam ser criadas antes do painel:

| O que falta | Onde criar |
|---|---|
| `GET /admin/renewals` | `api/routes/admin.py` |
| `GET /admin/claims` | `api/routes/admin.py` |
| `GET /admin/dashboard/summary` | nova rota — métricas agregadas |
| `GET /admin/agent-status` | nova rota — lê Redis para onboardings/sinistros ativos |
| Login/JWT | novo middleware ou rota `/auth/login` |

As rotas de clientes e apólices (`GET /admin/clients`, `GET /admin/policies`) já existem.

---

## Arquitetura

```
Next.js (porta 3000)               FastAPI (porta 8000)
  /login               →  POST /auth/login          → JWT
  /dashboard           →  GET  /admin/dashboard/summary
  /clients             →  GET  /admin/clients
  /clients/[id]        →  GET  /admin/clients/{id}
                           GET  /admin/policies?client_id={id}
                           GET  /admin/claims?client_id={id}
                           GET  /admin/renewals?client_id={id}
  /agent-status        →  GET  /admin/agent-status  → Redis
```

---

## Autenticação

Login simples com usuário e senha configurados no `.env`:

```env
DASHBOARD_USERNAME=corretor
DASHBOARD_PASSWORD=...
DASHBOARD_JWT_SECRET=...
```

JWT com expiração de 8h. Sem banco de usuários — corretor único.

---

## Questões resolvidas

| Questão | Decisão |
|---|---|
| Quem usa? | Corretor único |
| Como acessa? | Web (navegador) |
| Precisa de login? | Sim, JWT simples |
| Stack frontend? | React / Next.js |
| Deploy? | Container Docker separado ou Vercel |

---

## Fora do escopo (por enquanto)

- Edição de dados pelo painel (só visualização no MVP)
- Múltiplos usuários / controle de acesso por papel
- Relatórios exportáveis (PDF/Excel)
- Notificações em tempo real (WebSocket)
- Comissões (agente ainda não implementado)
