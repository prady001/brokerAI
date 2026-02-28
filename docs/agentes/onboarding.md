# Agente de Onboarding de Novos Clientes

## Objetivo

Conduzir o cadastro de um novo cliente via WhatsApp do início ao fim, sem que o corretor precise preencher nada manualmente. O agente coleta dados do cliente e da apólice por conversa, registra no banco e entrega ao vendedor um perfil completo pronto para operação.

O objetivo é transformar o onboarding — hoje feito por e-mail, planilha ou digitação manual — em uma conversa de 10 a 15 minutos no WhatsApp.

---

## Como funciona

### Fluxo principal

```
Corretor envia link ou inicia conversa com o novo cliente
          │
          ▼
  Orquestrador detecta intent = "onboarding"
  (ou cliente é identificado como novo — sem cadastro)
          │
          ▼
  collect_client_data
  (nome, CPF, telefone, e-mail)
          │
          ▼
  collect_policy_data
  (seguradora, ramo, produto, item, vigência, número de apólice)
          │
          ▼
  validate_data
  (verifica CPF válido, datas consistentes, campos obrigatórios)
          │
          ├── dados inválidos → solicita correção ao cliente
          │
          └── dados válidos
                    │
                    ▼
          register_client + register_policy
          (persiste no banco)
                    │
                    ▼
          send_welcome_summary
          (mensagem de boas-vindas ao cliente + resumo da apólice)
                    │
                    ▼
          notify_seller
          (resumo do novo cliente para o vendedor responsável)
```

### Dados coletados por etapa

**Etapa 1 — Dados do cliente**

| Campo | Obrigatório | Observação |
|---|---|---|
| Nome completo | ✅ | |
| CPF | ✅ | Validado com algoritmo de dígito verificador |
| Telefone WhatsApp | ✅ | Já disponível pela conversa |
| E-mail | ⬜ | Opcional no MVP |
| Data de nascimento | ⬜ | Coletado se disponível |

**Etapa 2 — Dados da apólice**

| Campo | Obrigatório | Observação |
|---|---|---|
| Seguradora | ✅ | Ex: Porto Seguro, Allianz |
| Ramo | ✅ | Automóvel, Residência, Vida, etc. |
| Produto | ✅ | Carro, Moto, Carta Verde, etc. |
| Item (descrição) | ✅ | Ex: "Toyota Yaris 1.3 Flex / Placa ABC1234" |
| Número da apólice | ✅ | |
| Vigência início | ✅ | |
| Vigência final | ✅ | Gatilho para o agente de renovação |
| Vendedor responsável | ✅ | Pré-configurado ou perguntado |

### Nós do grafo LangGraph

| Nó | Responsabilidade |
|---|---|
| `collect_client` | Coleta e valida dados pessoais via conversa |
| `collect_policy` | Coleta dados da apólice |
| `validate` | Valida CPF, datas e campos obrigatórios |
| `register` | Persiste `client` e `policy` no banco |
| `welcome` | Envia resumo de boas-vindas ao cliente |
| `notify_seller` | Envia resumo ao vendedor via WhatsApp |

### Tools implementadas

```python
@tool
def collect_client_data(conversation_id: str) -> dict:
    """
    Coleta nome, CPF, telefone e e-mail do cliente via conversa.
    Retorna os dados estruturados.
    """

@tool
def collect_policy_data(conversation_id: str, client_id: str) -> dict:
    """
    Coleta seguradora, ramo, produto, item, número de apólice e vigência.
    Retorna os dados estruturados.
    """

@tool
def validate_data(client_data: dict, policy_data: dict) -> dict:
    """
    Valida CPF (dígito verificador), datas de vigência e campos obrigatórios.
    Retorna: { valid: bool, errors: list[str] }
    """

@tool
def register_client(client_data: dict) -> str:
    """
    Persiste o cliente no banco. Retorna o client_id gerado.
    """

@tool
def register_policy(policy_data: dict, client_id: str) -> str:
    """
    Persiste a apólice no banco vinculada ao cliente.
    Retorna o policy_id gerado.
    """

@tool
def send_welcome_summary(client_id: str, policy_id: str) -> bool:
    """
    Envia mensagem de boas-vindas ao cliente com resumo da apólice cadastrada.
    """

@tool
def notify_seller(seller_phone: str, client_id: str, policy_id: str) -> bool:
    """
    Envia resumo do novo cliente ao vendedor responsável via WhatsApp.
    """
```

---

## Configuração

### Variáveis de ambiente

```env
# Vendedor padrão quando não informado (telefone WhatsApp)
ONBOARDING_DEFAULT_SELLER_PHONE=+5517999999999

# Campos obrigatórios para considerar o onboarding completo
ONBOARDING_REQUIRED_FIELDS=nome,cpf,seguradora,ramo,produto,item,numero_apolice,vigencia_final

# Número de tentativas antes de escalar para corretor em caso de dado inválido
ONBOARDING_MAX_RETRIES=3
```

### System prompt do agente

```
Você é o assistente da [Nome da Corretora] responsável por cadastrar novos clientes.
Seu objetivo é fazer o cadastro de forma agradável, como uma conversa, não como um formulário.

COMPORTAMENTO:
- Peça os dados um a um, de forma natural. Não liste tudo de uma vez.
- Se o cliente errar um dado (ex: CPF inválido), explique o erro de forma gentil e peça novamente.
- Confirme os dados ao final antes de cadastrar: repita tudo e peça uma confirmação.
- Após cadastrar, explique o que acontece a seguir (o corretor vai entrar em contato).

AÇÕES PROIBIDAS:
- Não cadastre sem confirmação explícita do cliente.
- Não prometa coberturas ou condições da apólice — apenas registre o que o cliente informa.
- Não peça dados sensíveis além do necessário (sem dados de cartão, conta bancária, etc.).
- Não se identifique como IA a menos que o cliente pergunte diretamente.
```

---

## Exemplos

### Exemplo 1 — Onboarding completo de novo segurado (automóvel)

```
Corretor: [envia link para o cliente]
          "Oi Alessandra! Te passei para o nosso assistente,
           ele vai fazer seu cadastro rapidinho. 😊"

Agente: Olá, Alessandra! Vou fazer seu cadastro aqui na corretora.
        Pode me confirmar seu nome completo?

Cliente: Alessandra Orlandi Camargo

Agente: Ótimo! E seu CPF?

Cliente: 123.456.789-00

Agente: Perfeito. Agora me conta sobre o seguro:
        qual é a seguradora e o veículo segurado?

Cliente: Ezze Seguros, Honda HR-V, placa GHG1590

Agente: Ótimo! Qual o número da apólice e a data de vencimento?

Cliente: Apólice 987654, vence em 16/08/2026

Agente: Vou confirmar tudo antes de finalizar:

        👤 Cliente: Alessandra Orlandi Camargo
        📄 CPF: 123.456.789-00
        📱 WhatsApp: (17) 98765-4321
        🚗 Veículo: Honda HR-V | GHG1590
        🏢 Seguradora: Ezze Seguros
        📋 Apólice: 987654
        📅 Vencimento: 16/08/2026

        Está tudo certo?

Cliente: Sim, pode cadastrar!

Agente: Feito! Seu cadastro está completo. ✅
        O Bernardo vai entrar em contato para confirmar os detalhes
        e te explicar como funciona o atendimento.
        Qualquer dúvida sobre o seguro, pode me chamar aqui!

[Notificação ao vendedor Bernardo]:
✅ NOVO CLIENTE CADASTRADO
Nome: Alessandra Orlandi Camargo
CPF: 123.456.789-00 | WhatsApp: (17) 98765-4321
Veículo: Honda HR-V | GHG1590 | Ezze Seguros
Apólice: 987654 | Vence: 16/08/2026
Cadastrado em: 16/08/2025 às 14h22
```

### Exemplo 2 — CPF inválido, correção solicitada

```
Agente: E seu CPF?

Cliente: 111.111.111-11

Agente: Hmm, esse CPF não parece válido — pode ter sido um erro de digitação.
        Consegue confirmar o número novamente?

Cliente: Ah desculpa! É 321.654.987-00

Agente: Esse está correto! Seguindo...
```

### Exemplo 3 — Dados incompletos, escala para corretor

```
[Após 3 tentativas sem conseguir o número da apólice]

Agente: Não consegui o número da apólice ainda — sem problema!
        Vou avisar o Bernardo para te ajudar a localizar essa informação.

[Notificação ao vendedor]:
⚠️ ONBOARDING INCOMPLETO — AÇÃO NECESSÁRIA
Cliente: Carlos Felipe de Carvalho | (17) 97654-3210
Dados faltantes: número da apólice (Suhai | Moto Suzuki GSX 650F)
Dados coletados: nome, CPF, veículo, seguradora
Ação: contatar cliente para coletar o número da apólice e finalizar cadastro.
```

---

## Limitações conhecidas

- **Sem OCR no MVP:** o cliente não pode enviar foto do documento para extração automática de dados. No MVP todos os dados são coletados por conversa. OCR (Mistral/Textract) é planejado para V1.
- **Sem validação de apólice na seguradora:** o agente registra o que o cliente informa, sem verificar se a apólice realmente existe no sistema da seguradora. Validação cruzada é planejada para V1.
- **Uma apólice por onboarding:** o fluxo cadastra uma apólice por sessão. Clientes com múltiplas apólices precisam iniciar um novo onboarding para cada uma.
- **Ramo limitado ao MVP:** o fluxo é otimizado para automóvel (carro e moto). Residência e seguro de vida são suportados mas sem perguntas específicas do ramo — apenas dados gerais.
- **Corretor pré-definido:** o agente usa o vendedor padrão configurado em `ONBOARDING_DEFAULT_SELLER_PHONE` a menos que o corretor informe outro no início da conversa.
