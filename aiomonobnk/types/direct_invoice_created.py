from datetime import datetime
from typing import Optional

from aiomonobnk.enums import CurrencyCode
from pydantic import Field

from .base import ClientObject
from ..enums.direct_payment_status import DirectPaymentStatus


class DirectInvoiceCreated(ClientObject):

    invoice_id: str = Field(alias='invoiceId')
    tds_url: Optional[str] = Field(alias='tdsUrl')
    status: DirectPaymentStatus
    failure_reason: Optional[str] = Field(alias='failureReason', default=None)
    amount: int
    ccy: CurrencyCode
    created_date: datetime = Field(alias='createdDate')
    modified_date: datetime = Field(alias='modifiedDate')
