"""
Nós do grafo LangGraph do Agente de Renovação.
Cada nó é uma função assíncrona que recebe e retorna um RenewalState.
Dependências (_renewal_service, _llm) são passadas via state — sem globals mutáveis.
"""
import logging
from datetime import date
from uuid import UUID

import services.notification_service as ns
from agents.renewal.prompts import (
    RENEWAL_SYSTEM_PROMPT,
    SELLER_NOTIFY_CONFIRMED,
    SELLER_NOTIFY_NEEDS_REVIEW,
    SELLER_NOTIFY_NO_RESPONSE,
    SELLER_NOTIFY_REFUSED,
    SELLER_NOTIFY_WANTS_QUOTE,
    TEMPLATE_15_7_DAYS,
    TEMPLATE_30_DAYS,
    TEMPLATE_DAY_ZERO,
)
from models.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
            corretora=settings.broker_name,
            item=item,
            dias=dias,
            data_vencimento=data_vencimento,
        )
    elif template_key == "15_7_days":
        return TEMPLATE_15_7_DAYS.format(nome=nome, item=item, dias=dias)
    else:
        produto = item.split("/")[0].strip() if "/" in item else item
        return TEMPLATE_DAY_ZERO.format(nome=nome, produto=produto)


# ---------------------------------------------------------------------------
# Nós do grafo
# ---------------------------------------------------------------------------

async def check_expiring_policies(state: dict) -> dict:
    """
    Identifica apólices nos gatilhos da régua (30/15/7/0 dias).
    Modo: cron
    """
    renewal_service = state.get("_renewal_service")
    if renewal_service is None:
        logger.error("RenewalService não injetado nos nós")
        return {**state, "errors": state.get("errors", []) + ["RenewalService não configurado"]}

    alert_days = [int(d) for d in settings.renewal_alert_days.split(",")]
    candidates = await renewal_service.get_expiring_policies(alert_days)

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
    renewal_service = state.get("_renewal_service")
    if renewal_service is None:
        return {**state, "errors": state.get("errors", []) + ["RenewalService não configurado"]}

    contacts_sent = []
    errors = list(state.get("errors", []))

    for candidate in state.get("policies_to_contact", []):
        try:
            renewal = await renewal_service.get_or_create_renewal(
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
                sent = False

            await renewal_service.register_contact_attempt(renewal.id)

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

    llm = state.get("_llm")
    if llm is None:
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
        intent = intent_raw if intent_raw in valid_intents else "needs_review"

        logger.info("Intenção classificada: %s → %s", client_response[:50], intent)
    except Exception as e:
        logger.error("Erro ao classificar intenção: %s", e)
        intent = "needs_review"

    return {**state, "intent": intent}


async def notify_sellers(state: dict) -> dict:
    """
    Notifica vendedores com resumo estruturado conforme intenção do cliente.
    Modo: whatsapp
    """
    renewal_service = state.get("_renewal_service")
    if renewal_service is None:
        return {**state, "errors": state.get("errors", []) + ["RenewalService não configurado"]}

    renewal_id = state.get("renewal_id")
    intent = state.get("intent")
    notifications_sent = []
    errors = list(state.get("errors", []))

    if not renewal_id:
        return {**state, "errors": errors + ["renewal_id ausente para notificação"]}

    detail = await renewal_service.get_renewal_with_details(UUID(renewal_id))
    if detail is None:
        return {**state, "errors": errors + [f"Renovação não encontrada: {renewal_id}"]}

    seller_phone = detail.renewal.seller_phone
    if not seller_phone:
        logger.warning("Sem telefone de vendedor para renewal_id=%s", renewal_id)
        return {**state, "notifications_sent": notifications_sent}

    data_vencimento = (
        detail.renewal.expiry_date.strftime("%d/%m/%Y") if detail.renewal.expiry_date else ""
    )
    common = dict(
        nome=detail.client_name,
        item=detail.item_description or "apólice",
        policy_number=detail.policy_number,
        seguradora=detail.insurer_name or "",
        data_vencimento=data_vencimento,
    )

    if intent == "wants_renewal":
        msg = SELLER_NOTIFY_CONFIRMED.format(**common)
    elif intent == "refused":
        notes = detail.renewal.intent_notes or "não informado"
        msg = SELLER_NOTIFY_REFUSED.format(
            nome=common["nome"],
            item=common["item"],
            policy_number=common["policy_number"],
            seguradora=common["seguradora"],
            motivo=notes,
        )
    elif intent == "wants_quote":
        msg = SELLER_NOTIFY_WANTS_QUOTE.format(**common)
    elif intent == "needs_review":
        msg = SELLER_NOTIFY_NEEDS_REVIEW.format(**common)
    else:
        count = detail.renewal.contact_count or 0
        tentativas_texto = f"{count} tentativa" if count == 1 else f"{count} tentativas"
        msg = SELLER_NOTIFY_NO_RESPONSE.format(**common, tentativas_texto=tentativas_texto)

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
    Modo cron: marca renovações vencidas como no_response via mark_overdue_renewals.
    Modo whatsapp: atualiza status conforme intenção registrada.
    """
    renewal_service = state.get("_renewal_service")
    if renewal_service is None:
        return {**state, "errors": state.get("errors", []) + ["RenewalService não configurado"]}

    errors = list(state.get("errors", []))
    renewal_id = state.get("renewal_id")
    intent = state.get("intent")

    # Modo whatsapp: atualiza status conforme intenção registrada
    if renewal_id and intent:
        status_map = {
            "wants_renewal": "confirmed",
            "refused": "refused",
            "wants_quote": "contacted",
            "needs_review": "contacted",
        }
        new_status = status_map.get(intent, "contacted")
        try:
            await renewal_service.update_renewal_status(
                UUID(renewal_id), status=new_status, intent=intent
            )
            logger.info("Status atualizado: renewal_id=%s → %s", renewal_id, new_status)
        except Exception as e:
            errors.append(f"Erro ao atualizar status {renewal_id}: {e}")

    # Modo cron: marca renovações vencidas sem resposta
    try:
        marked = await renewal_service.mark_overdue_renewals(settings.renewal_overdue_days)
        for rid in marked:
            logger.info("Renovação marcada como no_response: %s", rid)
    except Exception as e:
        errors.append(f"Erro ao verificar renovações vencidas: {e}")

    return {**state, "errors": errors}
