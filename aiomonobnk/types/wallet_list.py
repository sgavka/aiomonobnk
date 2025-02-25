from .base import ClientObject

from .wallet_item import WalletItem


class WalletList(ClientObject):
    wallet: list[WalletItem]
