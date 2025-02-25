from pydantic import Field

from .base import (
    ClientMethod,
    RequestMethod
)
from ..types.wallet_list import WalletList


class WalletCardsMethod(ClientMethod):
    __request_method__ = RequestMethod.GET
    __request_path__ = '/api/merchant/wallet'
    __returning__ = WalletList

    wallet_id: str = Field(alias='walletId')

    def __init__(
            self,
            wallet_id: str
    ):
        super().__init__(
            walletId=wallet_id
        )
