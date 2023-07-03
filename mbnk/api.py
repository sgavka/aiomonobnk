__all__ = [
    'MonobankOpenAPIModel',
    'MonobankCorporateOpenAPIModel',
    'MonoAcquiringAPIModel'
]

import re
import json
import requests

from enum import Enum

from requests import Response
from aiohttp import (
    ClientSession,
    ClientResponse
)
from typing import Union, Optional

from mbnk.exceptions import *

from mbnk.types import *

from mbnk.responses import *


class APIMethod:

    __api_token = None
    __headers = {}

    def __init__(
            self,
            base_url: str,
            api_token: str,
            _async: bool,
    ):
        self.__is_async: bool = _async
        self.__api_token: str = api_token
        self.__base_url: str = base_url
        self.__headers["X-Token"] = self.__api_token

    @staticmethod
    def __camel_to_underscore(text: str):
        camel_pat = re.compile(r'([A-Z])')
        return camel_pat.sub(lambda x: '_' + x.group(1).lower(), text)

    @staticmethod
    def __underscore_to_camel(text: str):
        under_pat = re.compile(r'_([a-z])')
        return under_pat.sub(lambda x: x.group(1).upper(), text)

    def __json_convert(self, data, convert):
        if isinstance(data, dict):
            new_data = {}
            for k, value in data.items():
                new_data[convert(k)] = self.__json_convert(value, convert) if (
                    isinstance(value, dict)
                ) else self.__json_convert(value, convert) if isinstance(value, list) else value
            return new_data
        elif isinstance(data, list):
            new_list = []
            for item in data:
                new_list.append(self.__json_convert(item, convert))
            return new_list

    def __load_response(self, response_data: Union[dict, list]):

        return self.__json_convert(response_data, self.__camel_to_underscore)

    def __build_data(self, **kwargs):
        data = {}

        for kwarg in kwargs:
            key = kwarg.replace("timestamp", "")
            key = self.__underscore_to_camel(key)
            value = kwargs.get(kwarg)
            data[key] = value

        return data

    @staticmethod
    def __is_exception(response: Union[Response, ClientResponse]) -> bool:
        if isinstance(response, Response):
            status_code = response.status_code
        elif isinstance(response, ClientResponse):
            status_code = response.status
        else:
            return True

        if status_code != 200:
            return True

        return False

    @staticmethod
    def __get_exception(response: Union[Response, ClientResponse]):
        if isinstance(response, Response):
            status_code = response.status_code
        elif isinstance(response, ClientResponse):
            status_code = response.status
        else:
            return

        if status_code == 400:
            raise Exception
        elif status_code == 403:
            raise Exception
        elif status_code == 404:
            raise Exception
        elif status_code == 429:
            raise TooManyRequestsException
        else:
            return MonoPayAPIException

    def __sync_request(
            self,
            method: str,
            path: str,
            data: str = None,
            params: str = None
    ):
        request = getattr(requests, method)
        response = request(
            url=f"{self.__base_url}/{path}",
            headers=self.__headers,
            params=params,
            data=json.dumps(data) if data is not None else None
        )
        response_data = response.json()
        response_data = self.__load_response(response_data)

        if self.__is_exception(response):
            raise self.__get_exception(response)

        return response_data

    async def __async_request(
            self,
            method: str,
            path: str,
            data: str = None,
            params: str = None
    ):
        async with ClientSession() as session:
            request = getattr(session, method)
            async with request(
                    url=f"{self.__base_url}/{path}",
                    headers=self.__headers,
                    data=json.dumps(data) if data is not None else None,
                    params=params
            ) as response:
                response_data = await response.json()
                response_data = self.__load_response(response_data)

                if self.__is_exception(response):
                    raise self.__get_exception(response)

                return response_data

    @staticmethod
    def _request(
            request_method: str,
            path: str
    ):
        def outer(func):
            def inner(*args, **kwargs):
                self = args[0]
                args = args[1:]
                func_args = {
                    "method": request_method,
                    "path": path,
                    ("params" if request_method == "get" else "data"): self.__build_data(**kwargs)
                }

                async def async_wrapper():
                    response = await self.__async_request(**func_args)

                    if isinstance(response, MonoPayAPIException) or isinstance(response, MonobankAPIException):
                        return response

                    return func(self, *args, **kwargs, response_data=response)

                def sync_wrapper():
                    response = self.__sync_request(**func_args)

                    return func(self, *args, **kwargs, response_data=response)

                if self.__is_async:
                    return async_wrapper()
                else:
                    return sync_wrapper()

            return inner

        return outer


class APIPaths(str, Enum):
    # Mono Acquiring API
    merchant_details = "merchant/details"
    merchant_statement = "merchant/statement"
    merchant_pubkey = "merchant/pubkey"

    invoice_create = "merchant/invoice/create"
    invoice_split = "merchant/invoice/split-payments"
    invoice_cancel = "merchant/invoice/cancel"
    invoice_status = "merchant/invoice/status"
    invoice_invalidation = "merchant/invoice/remove"
    invoice_info = "merchant/invoice/payment-info"
    invoice_finalize = "merchant/invoice/finalize"

    qr_list = "merchant/qr/list"
    qr_details = "merchant/qr/details"
    qr_reset_amount = "merchant/qr/reset-amount"

    wallet_cards = "merchant/wallet"
    wallet_payment = "merchant/wallet/payment"
    wallet_delete_card = "merchant/wallet/card"

    # Monobank Open API
    currencies_list = "bank/currency"

    personal_info = "personal/client-info"
    personal_webhook = "personal/webhook"
    personal_statement = "personal/statement/{account}/{from}/{to}"

    # Monobank Corporate Open API
    auth_registration = "personal/auth/registration"
    auth_status = "personal/auth/registration/status"

    corporate_webhook = "personal/corp/webhook"
    corporate_info = "personal/corp/settings"

    init_access = "personal/auth/request"
    check_access = "personal/auth/request"


# Monobank Open API
class Public(APIMethod):

    @APIMethod._request("get", path=APIPaths.currencies_list)
    def currency(self, **kwargs) -> Union[CurrencyRatesResponse, MonobankAPIException]:

        return CurrencyRatesResponse(
            list=[
                CurrencyListItem(
                    **item
                ) for item in kwargs['response_data']
            ]
        )


class Personal(APIMethod):

    @APIMethod._request("get", path=APIPaths.personal_info)
    def info(self, **kwargs) -> Union[ClientInfoResponse, MonobankAPIException]:
        """
        Source: https://api.monobank.ua/docs/#tag/Kliyentski-personalni-dani/paths/~1personal~1client-info/get

        :return:
        """

        return ClientInfoResponse(
            client_id=kwargs['response_data']['client_id'],
            name=kwargs['response_data']['name'],
            web_hook_url=kwargs['response_data']['web_hook_url'],
            permissions=kwargs['response_data']['permissions'],
            accounts=[
                Account(
                    **account
                ) for account in kwargs['response_data']['accounts']
            ],
            jars=[
                Jar(
                    **jar
                ) for jar in kwargs['response_data']['jars']
            ]
        )

    @APIMethod._request("post", path=APIPaths.personal_webhook)
    def set_webhook(self, web_hook_url: str) -> Union[EmptyResponse, MonobankAPIException]:
        """
        Source: https://api.monobank.ua/docs/#tag/Kliyentski-personalni-dani/paths/~1personal~1webhook/post

        :param web_hook_url:
        :return:
        """
        return EmptyResponse()

    @APIMethod._request("get", path=APIPaths.personal_statement)
    def statement(self, **kwargs) -> Union[StatementResponse, MonobankAPIException]:

        return StatementResponse(
            list=[
                Transaction(
                    **transaction
                ) for transaction in kwargs['response_data']
            ]
        )


class MonobankOpenAPIModel:

    __base_url = "https://api.monobank.ua"
    __api_token = None
    __headers = {}

    def __init__(self, api_token: str, _async: bool):
        self.__is_async = _async

        self.__api_token = api_token
        self.__headers["X-Token"] = self.__api_token

        self.public: Public = Public(
            api_token=self.__api_token,
            base_url=self.__base_url,
            _async=self.__is_async
        )

        self.personal: Personal = Personal(
            api_token=self.__api_token,
            base_url=self.__base_url,
            _async=self.__is_async
        )

    def get_api_token(self):
        return self.__api_token


class Client(APIMethod):

    @APIMethod._request("post", path=APIPaths.init_access)
    def init_access(self):
        pass

    @APIMethod._request("get", path=APIPaths.check_access)
    def check_access(self):
        pass


class Authorization(APIMethod):

    @APIMethod._request("post", path=APIPaths.auth_registration)
    def registration(self):
        pass

    @APIMethod._request("post", path=APIPaths.auth_status)
    def status(self):
        pass


class MonobankCorporateOpenAPIModel:

    __base_url: str = "https://api.monobank.ua"
    __api_token: str = None
    __headers: dict = {}

    def __init__(self, api_token: str, _async: bool):
        self.__is_async: bool = _async

        self.__api_token: str = api_token
        self.__headers["X-Token"] = self.__api_token__

        self.public: Public = Public(
            api_token=self.__api_token,
            base_url=self.__base_url,
            _async=self.__is_async
        )

        self.auth: Authorization = Authorization(
            api_token=self.__api_token,
            base_url=self.__base_url,
            _async=self.__is_async
        )

        self.client: Client = Client(
            api_token=self.__api_token,
            base_url=self.__base_url,
            _async=self.__is_async
        )

    def set_webhook(self):
        pass

    def info(self):
        pass

    def set_api_token(self):
        return self.__api_token

    def get_api_token(self):
        return self.__api_token


# MonoPay
class Merchant(APIMethod):

    @APIMethod._request("get", path=APIPaths.merchant_details)
    def details(self, **kwargs) -> Union[MerchantDetailsResponse, MonoPayAPIException]:
        """
        Mono Acquiring API: https://api.monobank.ua/docs/acquiring.html#/paths/~1api~1merchant~1details/get

        :return: MerchantDetailsResponse
        """

        return MerchantDetailsResponse(**kwargs["response_data"])

    @APIMethod._request("get", path=APIPaths.merchant_statement)
    def statement(
            self,
            from_timestamp: int,
            to_timestamp: Optional[int] = None,
            **kwargs
    ) -> Union[MerchantStatementResponse, MonoPayAPIException]:
        """
        Mono Acquiring API: https://api.monobank.ua/docs/acquiring.html#/paths/~1api~1merchant~1statement/get

        :param from_timestamp:
        :param to_timestamp:
        :param kwargs:
        :return:
        """

        return MerchantStatementResponse(
            list=[
                MerchantStatementItem(
                    **statement_item,
                    cancel_list=[
                        CancelListItem(
                            **cancel_item
                        ) for cancel_item in statement_item['cancel_list']
                    ] if "cancel_list" in statement_item else None
                ) for statement_item in kwargs['response_data']['list']
            ]
        )

    @APIMethod._request("get", path=APIPaths.merchant_pubkey)
    def pubkey(self, **kwargs) -> Union[MerchantPubKeyResponse, MonoPayAPIException]:
        """
        Mono Acquiring API Docs: https://api.monobank.ua/docs/acquiring.html#/paths/~1api~1merchant~1pubkey/get

        :return: MerchantPubKeyResponse
        """

        return MerchantPubKeyResponse(**kwargs["response_data"])


class Invoice(APIMethod):

    @APIMethod._request("post", path=APIPaths.invoice_create)
    def create(
            self,
            amount: int,
            ccy: Optional[int] = None,
            merchant_paym_info: Optional[MerchantPaymInfo] = None,
            redirect_url: Optional[str] = None,
            web_hook_url: Optional[str] = None,
            validity: Optional[int] = None,
            payment_type: Optional[str] = None,
            qr_id: Optional = None,
            save_card_data: Optional[SaveCardData] = None,
            **kwargs
    ) -> Union[InvoiceCreatedResponse, MonoPayAPIException]:
        """
        Mono Acquiring API: https://api.monobank.ua/docs/acquiring.html#/paths/~1api~1merchant~1invoice~1create/post

        :param amount:
        :param ccy:
        :param merchant_paym_info:
        :param redirect_url:
        :param web_hook_url:
        :param validity:
        :param payment_type:
        :param qr_id:
        :param save_card_data:
        :return:
        """

        return InvoiceCreatedResponse(**kwargs['response_data'])

    @APIMethod._request("post", path=APIPaths.invoice_split)
    def split(
            self,
            invoice_id: str,
            **kwargs
    ) -> Union[SplitInvoiceResponse, MonoPayAPIException]:
        """
        Mono Acquiring API:

        :param invoice_id:
        :param kwargs:
        :return:
        """

        return SplitInvoiceResponse(**kwargs['response_data'])

    @APIMethod._request("post", path=APIPaths.invoice_cancel)
    def cancel(
            self,
            invoice_id: str,
            ext_ref: str = None,
            amount: int = None,
            items=None,
            **kwargs
    ) -> Union[InvoiceCanceledResponse, MonoPayAPIException]:
        """
        Mono Acquiring API: https://api.monobank.ua/docs/acquiring.html#/paths/~1api~1merchant~1invoice~1cancel/post

        :param invoice_id:
        :param ext_ref:
        :param amount:
        :param items:
        :param kwargs:
        :return:
        """
        return InvoiceCanceledResponse(**kwargs['response_data'])

    def status(
            self,
            invoice_id: str,
            **kwargs
    ) -> Union[InvoiceStatusResponse, MonoPayAPIException]:
        """
        Mono Acquiring API: https://api.monobank.ua/docs/acquiring.html#/paths/~1api~1merchant~1invoice~1status?invoiceId=%7BinvoiceId%7D/get

        :param invoice_id:
        :param kwargs:
        :return:
        """

        return kwargs["response_data"]

    @APIMethod._request("post", path=APIPaths.invoice_invalidation)
    def invalidation(
            self,
            invoice_id: str,
            **kwargs
    ) -> Union[EmptyResponse, MonoPayAPIException]:
        """
        Source: https://api.monobank.ua/docs/acquiring.html#/paths/~1api~1merchant~1invoice~1remove/post

        :param invoice_id:
        :param kwargs:
        :return:
        """

        return EmptyResponse()

    @APIMethod._request("get", path=APIPaths.invoice_info)
    async def info(
            self,
            invoice_id: str,
            **kwargs
    ) -> Union[InvoiceInfoResponse, MonoPayAPIException]:
        """
        Source: https://api.monobank.ua/docs/acquiring.html#/paths/~1api~1merchant~1invoice~1payment-info?invoiceId=%7BinvoiceId%7D/get

        :param invoice_id:
        :param kwargs:
        :return:
        """

        return kwargs['response_data']

    @APIMethod._request("get", path=APIPaths.invoice_finalize)
    def finalize(
            self,
            invoice_id: str,
            amount: int,
            **kwargs
    ) -> Union[FinalizeInvoiceResponse, MonoPayAPIException]:
        """
        Source: https://api.monobank.ua/docs/acquiring.html#/paths/~1api~1merchant~1invoice~1finalize/post

        :param invoice_id:
        :param amount:
        :param kwargs:
        :return:
        """
        return FinalizeInvoiceResponse(
            **kwargs['response_data']
        )


class Qr(APIMethod):

    @APIMethod._request("get", path=APIPaths.qr_list)
    def list(self, **kwargs) -> Union[QrListResponse, MonoPayAPIException]:
        return QrListResponse(
            list=[
                QrListItem(
                    **qr
                ) for qr in kwargs['response']['list']
            ]
        )

    @APIMethod._request("post", path=APIPaths.qr_details)
    def details(
            self,
            qr_id: str,
            **kwargs
    ) -> Union[QrDetailsResponse, MonoPayAPIException]:
        """
        :param qr_id:
        :return:
        """
        return QrDetailsResponse(**kwargs['response_data'])

    @APIMethod._request("post", path=APIPaths.qr_reset_amount)
    def reset_amount(
            self,
            qr_id: str,
            **kwargs
    ) -> Union[EmptyResponse, MonoPayAPIException]:
        """
        :param qr_id:
        :return:
        """
        return EmptyResponse()


class Wallet(APIMethod):

    @APIMethod._request("get", path=APIPaths.wallet_cards)
    async def cards(
            self,
            wallet_id: str,
            **kwargs
    ):
        """
        Source: https://api.monobank.ua/docs/acquiring.html#/paths/~1api~1merchant~1wallet/get

        :param wallet_id:
        :param kwargs:
        :return:
        """
        return kwargs["response_data"]

    @APIMethod._request("post", path=APIPaths.wallet_payment)
    async def payment(self):
        """
        Source: https://api.monobank.ua/docs/acquiring.html#/paths/~1api~1merchant~1wallet~1payment/post
        :return:
        """
        pass

    @APIMethod._request("delete", path=APIPaths.wallet_delete_card)
    def delete_card(
            self,
            card_token: str,
            **kwargs
    ):
        """
        This method delete tokenized card from wallet
        Source: https://api.monobank.ua/docs/acquiring.html#/paths/~1api~1merchant~1wallet~1card/delete

        :param card_token:
        :param kwargs:
        :return:
        """
        return kwargs["response_data"]


class MonoAcquiringAPIModel:

    __base_url: str = "https://api.monobank.ua/api"
    __is_async: bool = False

    def __init__(self, api_token: str, _async: bool):

        self.__is_async: bool = _async
        self.__api_token: str = api_token

        self.merchant: Merchant = Merchant(
            api_token=self.__api_token,
            base_url=self.__base_url,
            _async=self.__is_async
        )

        self.invoice: Invoice = Invoice(
            api_token=self.__api_token,
            base_url=self.__base_url,
            _async=self.__is_async
        )

        self.qr: Qr = Qr(
            api_token=self.__api_token,
            base_url=self.__base_url,
            _async=self.__is_async
        )

        self.wallet: Wallet = Wallet(
            api_token=self.__api_token,
            base_url=self.__base_url,
            _async=self.__is_async
        )

    def get_api_token(self):
        return self.__api_token
