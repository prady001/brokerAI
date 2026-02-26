"""
GraphMemoryService — Serviço de memória em grafo temporal por cliente.

STATUS: Planejado para V1 (mês 6). Não implementado no MVP.

Este serviço encapsula a integração com Graphiti (Zep) e Neo4j para construir
e consultar o knowledge graph acumulativo de cada cliente da corretora.

Cada interação do agente com um cliente alimenta o grafo com novos eventos,
entidades e relações. O grafo persiste indefinidamente e cresce a cada conversa.

Referência arquitetural: docs/architecture.md §7
Casos de uso habilitados: UC-01, UC-03, UC-04, UC-05, UC-06 (ver docs/produto/casos-de-uso.md)
"""
from uuid import UUID


class GraphMemoryService:
    """
    Interface principal para operações no knowledge graph de clientes.

    Implementação planejada para V1 usando:
    - Graphiti (graphiti-core) como engine de temporal knowledge graph
    - Neo4j como backend de persistência do grafo
    - LangMem como SDK de integração com LangGraph
    """

    async def add_memory(self, client_id: UUID, content: str, metadata: dict) -> None:
        """
        Extrai entidades e relações do conteúdo e adiciona ao grafo do cliente.

        O Graphiti usa um LLM para identificar automaticamente:
        - Entidades (pessoa, apólice, seguradora, sinistro, endereço, etc.)
        - Relações entre entidades (tem_apolice, fez_sinistro, prefere, etc.)
        - Timestamps de cada evento (grafo temporal)

        Args:
            client_id: UUID do cliente no PostgreSQL
            content: Texto da interação (mensagem, resumo, evento)
            metadata: Contexto adicional (tipo de interação, agente, canal)
        """
        raise NotImplementedError("GraphMemoryService será implementado na V1")

    async def search(self, client_id: UUID, query: str, limit: int = 10) -> list[dict]:
        """
        Busca semântica + estrutural no grafo do cliente.

        Combina:
        - Similaridade vetorial (embeddings) para encontrar memórias relevantes
        - Traversal de grafo para incluir entidades relacionadas
        - Filtro temporal para priorizar memórias recentes

        Args:
            client_id: UUID do cliente
            query: Consulta em linguagem natural
            limit: Número máximo de resultados

        Returns:
            Lista de memórias relevantes ordenadas por relevância
        """
        raise NotImplementedError("GraphMemoryService será implementado na V1")

    async def get_client_context(self, client_id: UUID) -> dict:
        """
        Retorna o contexto completo do cliente para injeção no system prompt do agente.

        Inclui:
        - Apólices ativas e histórico
        - Sinistros recentes e em aberto
        - Preferências de comunicação
        - Score de relacionamento (churn risk, potencial de expansão)
        - Eventos de vida detectados
        - Histórico de negociações relevantes

        Args:
            client_id: UUID do cliente

        Returns:
            Dicionário estruturado com contexto do cliente
        """
        raise NotImplementedError("GraphMemoryService será implementado na V1")

    async def compute_relationship_scores(self, client_id: UUID) -> dict:
        """
        Calcula scores de saúde do relacionamento com o cliente.

        Scores calculados:
        - churn_risk: 0.0-1.0 (probabilidade de cancelamento)
        - expansion_potential: 0.0-1.0 (potencial de cross-sell/upsell)
        - implicit_nps: -1.0-1.0 (satisfação estimada pelo tom das mensagens)
        - lifetime_value_estimate: valor projetado em reais

        Args:
            client_id: UUID do cliente

        Returns:
            Dicionário com os quatro scores
        """
        raise NotImplementedError("GraphMemoryService será implementado na V1")

    async def detect_life_events(self, client_id: UUID) -> list[dict]:
        """
        Identifica eventos de vida detectados nas interações recentes.

        Exemplos de eventos:
        - Menção a filho tirando carteira → oportunidade de seguro auto
        - Mudança de endereço detectada → revisão de seguro residencial
        - Segundo sinistro de assistência em 6 meses → carro velho, oportunidade

        Args:
            client_id: UUID do cliente

        Returns:
            Lista de eventos detectados com tipo, data e oportunidade gerada
        """
        raise NotImplementedError("GraphMemoryService será implementado na V1")
