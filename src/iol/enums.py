from enum import StrEnum


class Country(StrEnum):
    ARG = "argentina"
    USA = "estados_Unidos"


class InstrumentType(StrEnum):
    OPTIONS = "opciones"


class Market(StrEnum):
    BCBA = "bCBA"


class OptionType(StrEnum):
    CALL = "CALL"
    PUT = "PUT"