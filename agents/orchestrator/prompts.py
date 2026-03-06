"""
Prompts do Agente Orquestrador.
"""

INTENT_DETECTION_PROMPT = """
Você é o orquestrador de atendimento de uma corretora de seguros.
Analise a mensagem do cliente e classifique em uma das categorias:

- "claim"      → sinistro, acidente, roubo, dano, guincho, pane, vidro quebrado, assistência
- "onboarding" → cadastro, registrar, novo cliente, quero me cadastrar, fazer meu cadastro
- "faq"        → dúvida geral sobre cobertura, vencimento, boleto, documentos, apólice
- "unknown"    → não identificado, reclamação, assunto fora do escopo, saudação sem contexto

Retorne apenas o JSON: {{"intent": "<categoria>", "confidence": <0.0-1.0>}}

Mensagem: {message}
"""
