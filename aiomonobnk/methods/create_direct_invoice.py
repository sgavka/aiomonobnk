from pydantic import Field

from aiomonobnk.enums import InitiationKind
from aiomonobnk.types import CardData
from .base import (
    ClientMethod,
    RequestMethod
)
from ..enums import (
    CurrencyCode,
    PaymentType
)
from ..types import (
    SaveCardData,
    MerchantPaymInfo
)
from ..types.direct_invoice_created import DirectInvoiceCreated


class CreateDirectInvoiceMethod(ClientMethod):
    __request_method__ = RequestMethod.POST
    __request_path__ = '/api/merchant/invoice/payment-direct'
    __returning__ = DirectInvoiceCreated

    amount: int
    ccy: CurrencyCode | None = None
    card_data: CardData = Field(alias='cardData')
    merchant_paym_info: MerchantPaymInfo | None = Field(alias='merchantPaymInfo', default=None)
    web_hook_url: str | None = Field(alias='webHookUrl', default=None)
    payment_type: PaymentType | None = Field(alias='paymentType', default=None)
    save_card_data: SaveCardData | None = Field(alias='saveCardData', default=None)
    redirect_url: str | None = Field(alias='redirectUrl', default=None)
    initiation_kind: InitiationKind = Field(alias='initiationKind')

    def __init__(
            self,
            amount: int,
            card_data: CardData,
            ccy: CurrencyCode | None = None,
            merchant_paym_info: MerchantPaymInfo | None = None,
            web_hook_url: str | None = None,
            payment_type: PaymentType | None = None,
            save_card_data: SaveCardData | None = None,
            redirect_url: str | None = None,
            initiation_kind: InitiationKind | None = None,
    ):
        super().__init__(
            amount=amount,
            ccy=ccy,
            cardData=card_data,
            merchantPaymInfo=merchant_paym_info,
            webHookUrl=web_hook_url,
            paymentType=payment_type,
            saveCardData=save_card_data,
            redirectUrl=redirect_url,
            initiationKind=initiation_kind
        )
