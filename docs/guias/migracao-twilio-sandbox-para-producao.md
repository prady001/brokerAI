# Migração: Twilio Sandbox → Número WhatsApp Aprovado

## Objetivo

Sair do sandbox do Twilio (limite de 50 mensagens/dia) para um número WhatsApp Business aprovado pela Meta, sem mudanças de código.

## Como funciona

O sandbox serve apenas para desenvolvimento. O número aprovado elimina o limite diário, habilita mensagens iniciadas pelo bot (via templates) e é o requisito para produção.

## Configuração

Única mudança necessária no `.env`:

```env
TWILIO_WHATSAPP_FROM=whatsapp:+55XXXXXXXXXXX  # novo número aprovado
```

## Checklist de Migração

### 1. Pré-requisitos
- [ ] Conta Twilio com cartão de crédito ativo
- [ ] Facebook Business Manager verificado — business.facebook.com
- [ ] Nome da empresa, endereço e CNPJ em mãos
- [ ] Número de telefone novo (não pode ser número que já usa WhatsApp pessoal)

### 2. Solicitar o número no Twilio
- [ ] Console → **Messaging → Senders → WhatsApp Senders → New Sender**
- [ ] Escolher "Use your own number" ou comprar um número Twilio
- [ ] Preencher o perfil do WhatsApp Business (nome, descrição, logo)
- [ ] Vincular ao Facebook Business Manager
- [ ] Submeter para aprovação Meta (1–3 dias úteis)

### 3. Mudanças no código
Apenas atualizar `TWILIO_WHATSAPP_FROM` no `.env` com o novo número.

### 4. Testar antes de ir pro ar
- [ ] Enviar mensagem de template para um número (exigido para fluxo push)
- [ ] Confirmar que webhook continua recebendo no URL correto
- [ ] Testar fluxo completo: onboarding, sinistro, renovação

### 5. Quando tiver VPS
- [ ] Trocar `cloudflared` por URL fixa com HTTPS (Nginx + Let's Encrypt)
- [ ] Atualizar webhook no Twilio para a URL de produção
- [ ] Remover `ENVIRONMENT=development` para ativar validação HMAC-SHA1

## Limitações conhecidas

- O fluxo push (`/cadastrar <numero>`) exige **template de mensagem aprovado pela Meta**. Mensagens iniciadas pelo bot precisam usar template; apenas respostas a mensagens do usuário são livres.
- Aprovação Meta pode levar até 3 dias úteis.
- Número usado no sandbox (`+14155238886`) não pode ser migrado — é compartilhado entre contas.
