"""
Nós do grafo LangGraph do Agente de Renovação.
Cada nó é uma função assíncrona que recebe e retorna um RenewalState.
"""
import logging
from datetime import date, timedelta

from agents.renewal.prompts import (
    RENEWAL_SYSTEM_PROMPT,
    SELLER_NOTIFY_CONFIRMED,
    SELLER_NOTIFY_NO_RESPONSE,
    SELLER_NOTIFY_REFUSED,
    SELLER_NOTIFY_WANTS_QUOTE,
    TEMPLATE_15_7_DAYS,
    TEMPLATE_30_DAYS,
    TEMPLATE_DAY_ZERO,
)

logger = logging.getLogger(__name__)

# Injetados antes do uso — ver graph.py
_renewal_service = None
_llm = None


def inject_node_dependencies(renewal_service, llm) -> None:  # type: ignore[no-untyped-def]
    global _renewal_service, _llm
    _renewal_service = renewal_service
    _llm = llm


def _select_template(days_until_expiry: int) -> str:
    if days_until_expiry >= 30:
        return "30_days"
    elif days_until_expiry >= 7:
        return "15_7_days"
    else:
        return "day_zero"


def _format_template(template_key: str, candidate: dict) -> str:
    """Formata o template com os dados do candidato."""
    item = candidate.get("item_description") or "apólice"
    nome = candidate.get("client_name", "")
    dias = candidate.get("days_until_expiry", 0)
    expiry_raw = candidate.get("expiry_date", "")
    try:
        expiry_date = date.fromisoformat(expiry_raw)
        data_vencimento = expiry_date.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        data_vencimento = expiry_raw

    if template_key == "30_days":
        return TEMPLATE_30_DAYS.format(
            nome=nome,
            corretora="sua corretora",
            item=item,
            dias=dias,
            data_vencimento=data_vencimento,
        )
    elif template_key == "15_7_days":
        return TEMPLATE_15_7_DAYS.format(nome=nome, item=item, dias=dias)
    else:
        produto = item.split("/")[0].strip() if "/" in item else item
        return TEMPLATE_DAY_ZERO.format(nome=nome, produto=produto)


async def check_expiring_policies(state: dict) -> dict:
    """
    Identifica apólices nos gatilhos da régua (30/15/7/0 dias).
    Modo: cron
    """
    if _renewal_service is None:
        logger.error("RenewalService não injetado nos nós")
        return {**state, "errors": state.get("errors", []) + ["RenewalService não configurado"]}

    from models.config import settings

    alert_days = [int(d) for d in settings.renewal_alert_days.split(",")]
    candidates = await _renewal_service.get_expiring_policies(alert_days)

    logger.info("Apólices elegíveis para contato: %d", len(candidates))
    return {
        **state,
        "policies_to_contact": [
            {
                "policy_id": str(c.policy_id),
                "client_id": str(c.client_id),
                "client_name": c.client_name,
                "client_phone": c.client_phone,
                "seller_phone": c.seller_phone,
                "policy_number": c.policy_number,
                "item_description": c.item_description,
                "expiry_date": c.expiry_date.isoformat(),
                "days_until_expiry": c.days_until_expiry,
                "renewal_id": str(c.renewal_id) if c.renewal_id else None,
            }
            for c in candidates
        ],
    }


async def send_contacts(state: dict) -> dict:
    """
    Envia mensagens WhatsApp para cada apólice elegível.
    Modo: cron
    """
    import services.notification_service as ns
    from uuid import UUID

    contacts_sent = []
    errors = list(state.get("errors", []))

    for candidate in state.get("policies_to_contact", []):
        try:
            # Cria ou busca o registro de renovação
            renewal = await _renewal_service.get_or_create_renewal(  # type: ignore[union-attr]
                policy_id=UUID(candidate["policy_id"]),
                client_id=UUID(candidate["client_id"]),
                seller_phone=candidate.get("seller_phone"),
                expiry_date=date.fromisoformat(candidate["expiry_date"]),
            )

            template_key = _select_template(candidate["days_until_expiry"])
            message = _format_template(template_key, candidate)

            try:
                await ns.send_whatsapp_message(candidate["client_phone"], message)
                sent = True
            except NotImplementedError:
                logger.warning(
                    "Evolution API não configurada — simulando envio para %s",
                    candidate["client_phone"],
                )
                sent = False  # Simula sem erro em dev

            await _renewal_service.register_contact_attempt(renewal.id)  # type: ignore[union-attr]

            contacts_sent.append({
                "renewal_id": str(renewal.id),
                "client_phone": candidate["client_phone"],
                "template": template_key,
                "sent": sent,
            })
            logger.info(
                "Contato enviado: cliente=%s template=%s", candidate["client_name"], template_key
            )
        except Exception as e:
            logger.error("Erro ao enviar contato para policy_id=%s: %s", candidate["policy_id"], e)
            errors.append(f"policy_id={candidate['policy_id']}: {e}")

    return {**state, "contacts_sent": contacts_sent, "errors": errors}


async def process_client_response(state: dict) -> dict:
    """
    Processa resposta do cliente via WhatsApp e extrai intenção usando LLM.
    Modo: whatsapp
    """
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import HumanMessage, SystemMessage

    client_response = state.get("client_response", "")
    renewal_id = state.get("renewal_id")

    if not client_response or not renewal_id:
        return {**state, "errors": state.get("errors", []) + ["Resposta ou renewal_id ausente"]}

    # Usa o LLM injetado ou cria um padrão
    llm = _llm
    if llm is None:
        from models.config import settings
        llm = ChatAnthropic(model="claude-haiku-4-5-20251001", api_key=settings.anthropic_api_key)  # type: ignore[call-arg]

    classification_prompt = f"""Classifique a resposta do cliente em uma das três categorias:
- wants_renewal: o cliente quer renovar a apólice
- refused: o cliente não quer renovar
- wants_quote: o cliente quer cotação em outra seguradora

Resposta do cliente: "{client_response}"

Responda com apenas uma palavra: wants_renewal, refused ou wants_quote."""

    try:
        response = await llm.ainvoke([
            SystemMessage(content=RENEWAL_SYSTEM_PROMPT),
            HumanMessage(content=classification_prompt),
        ])
        intent_raw = response.content.strip().lower()  # type: ignore[union-attr]

        valid_intents = {"wants_renewal", "refused", "wants_quote"}
        intent = intent_raw if intent_raw in valid_intents else "wants_renewal"

        logger.info("Intenção classificada: %s → %s", client_response[:50], intent)
    except Exception as e:
        logger.error("Erro ao classificar intenção: %s", e)
        intent = "wants_renewal"  # fallback conservador

    return {**state, "intent": intent}


async def notify_sellers(state: dict) -> dict:
    """
    Notifica vendedores com resumo estruturado conforme intenção do cliente.
    Modo: whatsapp
    """
    import services.notification_service as ns

    renewal_id = state.get("renewal_id")
    intent = state.get("intent")
    notifications_sent = []
    errors = list(state.get("errors", []))

    if not renewal_id:
        return {**state, "errors": errors + ["renewal_id ausente para notificação"]}

    from uuid import UUID
    renewal = await _renewal_service.get_renewal_by_id(UUID(renewal_id))  # type: ignore[union-attr]
    if renewal is None:
        return {**state, "errors": errors + [f"Renovação não encontrada: {renewal_id}"]}

    seller_phone = renewal.seller_phone
    if not seller_phone:
        logger.warning("Sem telefone de vendedor para renewal_id=%s", renewal_id)
        return {**state, "notifications_sent": notifications_sent}

    # Monta resumo conforme intenção
    notes = renewal.intent_notes or "não informado"
    if intent == "wants_renewal":
        msg = SELLER_NOTIFY_CONFIRMED.format(
            nome="cliente",
            item=str(renewal.expiry_date),
            policy_number="",
            seguradora="",
            data_vencimento=renewal.expiry_date.strftime("%d/%m/%Y") if renewal.expiry_date else "",
        )
    elif intent == "refused":
        msg = SELLER_NOTIFY_REFUSED.format(
            nome="cliente",
            item="apólice",
            policy_number="",
            seguradora="",
            motivo=notes,
        )
    elif intent == "wants_quote":
        msg = SELLER_NOTIFY_WANTS_QUOTE.format(
            nome="cliente",
            item="apólice",
            policy_number="",
            seguradora="",
            data_vencimento=renewal.expiry_date.strftime("%d/%m/%Y") if renewal.expiry_date else "",
        )
    else:
        msg = SELLER_NOTIFY_NO_RESPONSE.format(
            nome="cliente",
            item="apólice",
            policy_number="",
            seguradora="",
            data_vencimento=renewal.expiry_date.strftime("%d/%m/%Y") if renewal.expiry_date else "",
            tentativas=renewal.contact_count or 0,
        )

    try:
        await ns.send_whatsapp_message(seller_phone, msg)
        notifications_sent.append({"renewal_id": renewal_id, "seller_phone": seller_phone})
        logger.info("Vendedor notificado: renewal_id=%s intent=%s", renewal_id, intent)
    except NotImplementedError:
        logger.warning("Evolution API não configurada — notificação ao vendedor simulada")
    except Exception as e:
        logger.error("Erro ao notificar vendedor: %s", e)
        errors.append(str(e))

    return {**state, "notifications_sent": notifications_sent, "errors": errors}


async def update_statuses(state: dict) -> dict:
    """
    Atualiza status de renovações com base no resultado do ciclo.
    Aplica regra de no_response para renovações no dia 0 sem resposta.
    Modo: cron e whatsapp
    """
    from uuid import UUID

    errors = list(state.get("errors", []))
    renewal_id = state.get("renewal_id")
    intent = state.get("intent")

    # Modo whatsapp: atualiza status conforme intenção registrada
    if renewal_id and intent:
        status_map = {
            "wants_renewal": "confirmed",
            "refused": "refused",
            "wants_quote": "contacted",
        }
        new_status = status_map.get(intent, "contacted")
        try:
            await _renewal_service.update_renewal_status(  # type: ignore[union-attr]
                UUID(renewal_id), status=new_status, intent=intent
            )
            logger.info("Status atualizado: renewal_id=%s → %s", renewal_id, new_status)
        except Exception as e:
            errors.append(f"Erro ao atualizar status {renewal_id}: {e}")

    # Modo cron: verifica renovações no dia 0 que passaram da data limite sem resposta
    from models.config import settings
    overdue_days = settings.renewal_overdue_days
    today = date.today()

    for contact in state.get("contacts_sent", []):
        r_id = contact.get("renewal_id")
        if not r_id:
            continue
        try:
            renewal = await _renewal_service.get_renewal_by_id(UUID(r_id))  # type: ignore[union-attr]
            if (
                renewal
                and renewal.status == "contacted"
                and renewal.expiry_date
                and (today - renewal.expiry_date).days >= overdue_days
            ):
                await _renewal_service.update_renewal_status(renewal.id, status="no_response")
                logger.info("Renovação marcada como no_response: %s", r_id)
        except Exception as e:
            errors.append(f"Erro ao verificar vencimento {r_id}: {e}")

    return {**state, "errors": errors}
