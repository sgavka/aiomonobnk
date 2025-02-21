from enum import StrEnum


class DirectPaymentStatus(StrEnum):
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILURE = "failure"
