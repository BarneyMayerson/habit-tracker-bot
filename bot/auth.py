import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from typing import Any

from bot.config import get_settings

settings = get_settings()


def verify_telegram_init_data(init_data: dict[str, Any]) -> bool:
    """
    Verify authenticity of data received from Telegram Login Widget.
    Official algorithm: https://core.telegram.org/widgets/login#checking-authorization
    """
    received_hash = init_data.pop("hash", None)
    if not received_hash:
        return False

    auth_date = datetime.fromtimestamp(int(init_data["auth_date"]), tz=UTC)
    if datetime.now(UTC) - auth_date > timedelta(days=1):
        return False

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(init_data.items()))
    secret_key = hashlib.sha256(settings.bot_token.encode()).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(calculated_hash, received_hash)
