from typing import Optional

from pydantic import Field

from .base import ClientObject


class WalletItem(ClientObject):
    card_token: str = Field(alias="cardToken")
    masked_pan: str = Field(alias="maskedPan")
    country: Optional[str] = Field(alias="country", default=None)
