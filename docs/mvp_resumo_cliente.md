# MVP — Agentes de IA para Corretora de Seguros

> **Para:** [Nome da cliente]
> **Data:** Fevereiro de 2026
> **Objetivo:** Alinhar escopo do MVP e coletar informações para iniciar a implementação

---

## O que vamos construir

Dois agentes de inteligência artificial operando pelo WhatsApp da corretora, cobrindo os dois processos de maior esforço operacional identificados na nossa conversa.

---

### Agente 1 — Comissionamento

**O que ele vai fazer:**

1. Todos os dias, acessa automaticamente os portais das seguradoras com as credenciais da corretora
2. Verifica se há novas comissões disponíveis
3. Baixa e consolida os dados de todas as seguradoras em um único relatório
4. Emite a nota fiscal de serviços automaticamente, sem intervenção humana
5. Envia o resumo do dia pelo WhatsApp para a corretora

**O que muda na prática:** o processo que hoje exige acessar N portais manualmente, copiar dados e emitir NF vira uma notificação automática no WhatsApp toda manhã.

---

### Agente 2 — Sinistros

**O que ele vai fazer:**

1. Recebe a mensagem do cliente no WhatsApp da corretora
2. Identifica que é um sinistro e coleta as informações necessárias (tipo, localização, dados da apólice)
3. Abre o chamado na seguradora pelo canal adequado
4. Repassa as respostas e atualizações diretamente para o cliente
5. Mantém o histórico centralizado até o encerramento do caso

**O que muda na prática:** a corretora sai do meio da conversa. O copia-e-cola entre cliente e seguradora é eliminado. A equipe só é acionada em casos que realmente precisam de julgamento humano.

---

## O que fica fora do MVP

Para entregar rápido e com qualidade, o MVP não inclui:

- Renovação de apólices (segunda fase)
- Captação de novos clientes (segunda fase)
- Dashboard de gestão e relatórios (segunda fase)
- Integração direta com o Agger
- Emissão de apólices pelo agente

---

## Perguntas essenciais — precisamos das respostas para começar

### Sobre as seguradoras

1. Com quais seguradoras a corretora trabalha atualmente? (liste todas, mesmo as menores)
2. Para cada uma: o acesso ao portal é por login e senha? Tem código de verificação (SMS ou e-mail) no login?
3. Tem alguma seguradora com quem a comunicação de sinistro é feita por WhatsApp? Qual é o número?
4. Para as demais: como a corretora abre um sinistro hoje — portal, telefone ou e-mail?

### Sobre o Agger

5. No Agger, é possível exportar a lista de apólices ativas? (em Excel ou CSV)
6. Quais informações aparecem nessa exportação? (nome do cliente, número da apólice, seguradora, vencimento, prêmio)
7. Com que frequência os dados do Agger são atualizados?

### Sobre comissões

8. Quando uma comissão fica disponível no portal da seguradora, ela aparece como tabela na tela, PDF para baixar ou planilha?
9. A nota fiscal de serviços é emitida em qual prefeitura? (cidade do CNPJ da corretora)
10. Hoje a NF é emitida no portal da prefeitura diretamente ou por algum sistema contábil?

### Sobre o WhatsApp

11. A corretora usa um número de WhatsApp comercial (WhatsApp Business) ou número pessoal para atender clientes?
12. Esse número é exclusivo da corretora ou também é usado pessoalmente por alguém da equipe?
13. Os clientes já entram em contato por esse WhatsApp hoje para sinistros?

### Sobre a equipe

14. Quem faz a baixa de comissão hoje? É uma pessoa específica ou qualquer um da equipe?
15. Quem atende os sinistros pelo WhatsApp atualmente?
16. Há algum horário de preferência para receber o resumo diário de comissões?

---

## Próximos passos

Com as respostas acima, conseguimos:

1. Mapear exatamente quais portais de seguradoras precisam ser integrados
2. Confirmar se cada seguradora tem API ou se usaremos automação de browser
3. Configurar o número de WhatsApp da corretora
4. Definir o ambiente de testes com dados reais
5. Iniciar o desenvolvimento do Agente de Comissionamento (estimativa: 4–6 semanas para o primeiro agente funcionando)

---

*Qualquer dúvida sobre essas perguntas, estamos à disposição.*
