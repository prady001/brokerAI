# Pré-requisitos para Início da Implementação

> **Última atualização:** Fevereiro de 2026
> **Status:** Aguardando reunião com cliente e decisões técnicas

---

## Bloqueadores Absolutos — sem isso não dá para começar

| # | O que falta | Como desbloquear |
|---|---|---|
| 1 | Lista das 10 seguradoras prioritárias + tipo de acesso de cada uma | Reunião com o cliente |
| 2 | Credenciais de acesso a pelo menos 2 portais de seguradora (para testar) | Reunião com o cliente |
| 3 | Esclarecimento sobre NFS-e — como emitem hoje e cidade do CNPJ | Reunião com o cliente |
| 4 | Número de WhatsApp Business da corretora ou decisão de criar um | Reunião com o cliente |
| 5 | Exportação CSV do Agger com a carteira de apólices ativas | Reunião com o cliente |

---

## Bloqueadores Técnicos — decisões antes de codar

| # | O que falta | Decisão necessária |
|---|---|---|
| 6 | Ambiente de deploy — Railway ou AWS? | Railway é mais simples e barato para MVP. AWS dá mais controle. |
| 7 | Conta Z-API criada — instância do WhatsApp Business | Criar em z-api.io (≈ R$ 100/mês) |
| 8 | Conta Focus NFe criada — para emissão de NFS-e | Criar em focusnfe.com.br |
| 9 | Conta LangSmith criada — para rastreabilidade dos agentes | Gratuito até certo volume |
| 10 | Conta Sentry criada — para monitoramento de erros | Gratuito no tier básico |

---

## Pode Começar em Paralelo — não bloqueia o M1

| # | O que pode fazer agora |
|---|---|
| 11 | Subir o ambiente local: `docker compose up postgres redis -d` |
| 12 | Criar as migrations iniciais (estrutura das tabelas já está definida) |
| 13 | Configurar o CI/CD no GitHub Actions |
| 14 | Estruturar os modelos SQLAlchemy |

---

## Caminho Crítico

```
Reunião com cliente  →  Desbloqueios técnicos  →  M1 começa
    (esta semana)           (1-2 dias)             (semana 1)
```

A reunião com o cliente desbloqueia os 5 pontos mais importantes de uma vez.

---

## Perguntas para a Reunião com o Cliente

Ver documento completo: [`docs/produto/roteiro-reuniao-cliente.md`](./roteiro-reuniao-cliente.md)

### Bloco 1 — Seguradoras e Comissionamento

1. Das 50 seguradoras cadastradas, quais são as que mais geram comissão? Listar as 10 principais em ordem de volume.
2. Para cada uma: o acesso é por login e senha no portal, por e-mail ou tem API de corretor?
3. Alguma seguradora exige código de verificação no login? (SMS, e-mail ou autenticador?)
4. O dado de comissão aparece como tabela na tela, PDF ou planilha (Excel/CSV)?
5. Para as que mandam por e-mail: qual endereço recebe? Pode criar um e-mail dedicado para o agente?
6. Os dados têm sempre: segurado, apólice, seguradora, competência e valor?
7. Como emitem NFS-e hoje? Site da prefeitura, sistema contábil ou pelo contador?
8. Qual é a cidade do CNPJ da corretora?
9. A NF é emitida uma por seguradora ou uma por apólice?

### Bloco 2 — Sinistros

10. Já atendem clientes por WhatsApp? Existe número Business?
11. Topam criar um número de WhatsApp dedicado para o atendimento automatizado?
12. Como acompanham sinistros abertos no portal da seguradora? Tem lista diária?
13. O contato com a oficina é feito pela seguradora ou pela corretora?
14. Como as atualizações do portal chegam até o cliente hoje? Quem envia?
15. Além de auto e residencial, tem outros ramos relevantes?
16. Nos sinistros residenciais, o fluxo é parecido com o auto?
17. O status dos sinistros no Agger é manual ou sincroniza com as seguradoras?
18. Consigo exportar do Agger a carteira completa de apólices ativas? Quais campos?

### Bloco 3 — Acesso e Credenciais

19. Tem alguém de TI ou responsável pelo Agger para perguntas técnicas?
20. Consigo acesso a portais de pelo menos 2 seguradoras prioritárias para testes?
21. Alguma seguradora tem API para corretores? (Bradesco, Porto Seguro, etc.)
