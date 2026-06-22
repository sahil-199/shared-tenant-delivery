import logging

logger = logging.getLogger(__name__)


def send_whatsapp(phone: str, template: str, params: dict) -> None:
    # ponytail: dev stub — swap body to call Interakt/WATI/Gupshup when ready
    logger.info(f"[WhatsApp] TO:{phone} TEMPLATE:{template} PARAMS:{params}")
