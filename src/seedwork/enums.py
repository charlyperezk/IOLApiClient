from enum import StrEnum


class RequestMethod(StrEnum):
    GET = "GET"
    POST = "POST"


class ExtractionType(StrEnum):
    REGULAR = "REGULAR"


class ExtractionStatus(StrEnum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
