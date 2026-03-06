"""
State schema do Agente de Onboarding.
"""
from typing import TypedDict


class OnboardingState(TypedDict):
    # Identificação
    conversation_id: str
    client_phone: str           # número do cliente sendo cadastrado
    push_mode: bool             # True = iniciado pelo corretor via /cadastrar

    # Dados coletados em conversa
    client_data: dict           # full_name, cpf, email
    policy_data: dict           # insurer, policy_type, item_description, policy_number, end_date, start_date

    # Controle de fluxo
    client_data_complete: bool
    policy_data_complete: bool
    validation_errors: list[str]
    retry_count: int            # tentativas de correção de dados inválidos

    # Resultado
    client_id: str              # gerado após registro no banco
    policy_id: str              # gerado após registro no banco
    registered: bool
    failed: bool                # onboarding cancelado ou falhou após max retries

    # Conversa
    messages: list[dict]        # histórico: [{role, content, ts?}]
    status: str                 # collecting_client | collecting_policy | validating | registered | failed
