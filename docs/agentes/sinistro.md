# Agente de Sinistro Simples — E2E

## Objetivo

Atender o cliente que aciona o seguro via WhatsApp e conduzir o sinistro simples do início ao encerramento sem intervenção humana. O agente coleta os dados, abre o chamado na seguradora, repassa atualizações ao cliente e confirma o encerramento.

Sinistros graves (colisão com vítima, furto, incêndio) são escalados imediatamente para o corretor humano com um resumo estruturado.

---

## Como funciona

### Classificação de sinistros

| Categoria | Tipos | Tratamento |
|---|---|---|
| **Simples** | Guincho, pane seca, troca de pneu, vidros, assistência 24h, pequenos danos | Agente resolve E2E |
| **Grave** | Colisão com terceiros, furto/roubo, incêndio, acidente com vítima | Escala imediata para corretor |

### Fluxo principal (sinistro simples)

```
Cliente manda mensagem no WhatsApp
          │
          ▼
  Orquestrador detecta intent = "sinistro"
          │
          ▼
  collect_claim_info
  (tipo, localização, placa ou número de apólice)
          │
          ▼
  classify_claim
          │
          ├── severity = "grave" ──────────────────────────────────────────┐
          │                                                                 ▼
          └── severity = "simple"                              escalate_to_broker
                    │                                          (resumo estruturado)
                    ▼                                                       │
          open_claim_at_insurer                              Cliente recebe aviso
          (via API ou WhatsApp relay)                        que corretor assumiu
                    │
                    ▼
          relay_update_to_client
          (repassa protocolo e prazo estimado)
                    │
                    ▼ (aguarda seguradora)
          relay_update_to_client
          (repassa atualizações até encerramento)
                    │
                    ▼
          store_claim_history
          (registra no banco + fecha conversa)
```

### Nós do grafo LangGraph

| Nó | Responsabilidade |
|---|---|
| `collect_info` | Coleta tipo do sinistro, localização, placa/apólice via conversa |
| `classify` | Determina `severity` e `auto_resolve` |
| `open_claim` | Abre chamado na seguradora (API ou relay WhatsApp) |
| `relay_update` | Repassa status da seguradora ao cliente |
| `escalate` | Notifica corretor com resumo + para de atender |
| `close_claim` | Confirma encerramento com cliente e salva histórico |

### Tools implementadas

```python
@tool
def classify_claim(claim_type: str, description: str) -> dict:
    """
    Classifica o sinistro em simples ou grave.
    Simples: guincho, pane, troca de pneu, vidros, pequenos danos.
    Grave: colisão com terceiros, furto/roubo, incêndio, acidente com vítima.
    Retorna: { severity: 'simple' | 'grave', auto_resolve: bool }
    """

@tool
def collect_claim_info(conversation_id: str) -> dict:
    """
    Coleta dados mínimos necessários: tipo, localização, placa/apólice.
    Retorna os dados coletados estruturados.
    """

@tool
def open_claim_at_insurer(claim_id: str, insurer_id: str, claim_info: dict) -> dict:
    """
    Abre chamado na seguradora via canal configurado (API ou WhatsApp relay).
    Retorna: { thread_id: str, channel: str, opened_at: datetime }
    """

@tool
def relay_update_to_client(conversation_id: str, update: str, source: str) -> bool:
    """
    Repassa atualização da seguradora ao cliente via WhatsApp.
    """

@tool
def escalate_to_broker(claim_id: str, reason: str, summary: dict) -> bool:
    """
    Notifica corretor humano com resumo estruturado do sinistro.
    summary: { client, policy, claim_type, description, timeline }
    """

@tool
def store_claim_history(claim_id: str, outcome: str, timeline: list) -> bool:
    """
    Persiste o histórico completo do sinistro no banco ao encerrar.
    """
```

---

## Configuração

### Variáveis de ambiente

```env
# Tipos de sinistro que o agente resolve automaticamente (sem escalar)
CLAIM_AUTO_RESOLVE_TYPES=guincho,pane_seca,troca_pneu,vidro,assistencia_24h

# Timeout em horas para aguardar retorno da seguradora antes de alertar o corretor
CLAIM_INSURER_TIMEOUT_HOURS=4

# Canal de abertura de sinistros por seguradora (api | whatsapp_relay | manual)
# Configurado em config/insurers.json
CLAIM_DEFAULT_CHANNEL=whatsapp_relay
```

### System prompt do agente

```
Você é o assistente de sinistros da [Nome da Corretora].
Seu papel é ajudar o cliente a acionar o seguro de forma rápida e tranquila.

COMPORTAMENTO:
- Seja empático. Clientes em sinistro geralmente estão estressados.
- Colete as informações necessárias de forma natural, não como um formulário.
- Para guincho e assistência: agilidade é prioridade — colete o mínimo e acione.
- Para casos graves: seja claro que um corretor especializado vai assumir o caso.
- Nunca prometa prazos ou valores que não foram confirmados pela seguradora.

AÇÕES PROIBIDAS:
- Não tente resolver sinistros graves sem escalar para humano.
- Não prometa indenizações ou coberturas sem confirmação da seguradora.
- Não se identifique como IA a menos que o cliente pergunte diretamente.
```

---

## Exemplos

### Exemplo 1 — Guincho (sinistro simples, E2E)

```
Cliente: Oi, meu carro pifou na estrada, preciso de guincho

Agente: Oi, Eduardo! Vou acionar o guincho agora.
        Me diz a placa do carro e onde você está?

Cliente: Placa ABC1234, tô na Rodovia Anhanguera km 87 sentido interior

Agente: Perfeito! Encontrei sua apólice — Porto Seguro, Toyota Corolla.
        Já abri o chamado de assistência. Protocolo: PS-2025-0047821.
        O guincho tem previsão de chegada em 45 minutos.
        Vou te avisando qualquer atualização por aqui.

[40 minutos depois]

Agente: Eduardo, o guincho está a 5 minutos de você.
        O motorista vai se chamar Carlos, placa MNO9876.

[Após conclusão]

Agente: Tudo certo! O chamado foi encerrado pela Porto Seguro.
        Qualquer outra dúvida é só chamar. 🚗
```

### Exemplo 2 — Colisão com terceiro (sinistro grave, escalada)

```
Cliente: Tive um acidente, bati em outro carro, a outra pessoa ficou ferida

Agente: Entendo, deve estar sendo um momento difícil.
        Por segurança, vou passar seu caso direto para o Bernardo,
        que é especialista em sinistros graves.

        Enquanto isso: se precisar de socorro médico, ligue 192 (SAMU).

        [Notificação ao corretor Bernardo]:
        ⚠️ SINISTRO GRAVE — AÇÃO IMEDIATA
        Cliente: Luciana Garcia | (17) 99123-4567
        Seguro: VW Fox | EAL1I66 | Liberty
        Tipo: Colisão com terceiros, vítima confirmada
        Hora: 14h32 | Local: ainda não coletado
        ⚡ Cliente aguardando contato.
```

### Exemplo 3 — Upload de foto para vidro trincado

```
Cliente: Meu para-brisa trincou, preciso trocar

Agente: Oi! Vou abrir o chamado de vidro.
        Pode me mandar uma foto do para-brisa e me diz a placa?

Cliente: [envia foto] Placa EXW7H54

Agente: Recebi a foto! Apólice encontrada — Toyota Yaris, Alfa Seguros.
        Já abri o chamado. Protocolo: AL-2025-0018934.
        Uma assistência técnica vai entrar em contato em até 24h para agendar a troca.
        Pode ser no seu endereço ou no estabelecimento de sua preferência.
```

---

## Limitações conhecidas

- **Abertura de chamado no MVP:** no MVP, a abertura na seguradora é feita via WhatsApp relay (agente envia mensagem para o canal da seguradora) ou manualmente pelo corretor após receber o resumo. Integração via API é planejada para V1 (Porto Seguro e Tokio Marine).
- **Monitoramento de status:** no MVP o agente não monitora o portal da seguradora automaticamente — as atualizações são repassadas conforme chegam pelo canal de atendimento. Monitoramento ativo (RPA) é V1.
- **Fotos e documentos:** armazenados no Cloudflare R2. O agente não faz OCR no MVP — apenas armazena e envia à seguradora.
- **Sinistros sem apólice cadastrada:** se a placa ou número da apólice não estiver no banco, o agente coleta os dados e escala para o corretor cadastrar manualmente.
- **Horário de atendimento da seguradora:** o agente não controla o horário de funcionamento do atendimento da seguradora. Sinistros abertos fora do horário ficam em espera e o cliente é avisado.
