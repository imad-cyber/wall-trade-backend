"""Curated PSX symbol universe used when csapis /market/tickers is unavailable."""

from typing import Any

# Major PSX equities and indices — enough for search autocomplete until tickers API is enabled.
PSX_SYMBOL_UNIVERSE: list[dict[str, str]] = [
    {"ticker": "OGDC", "name": "Oil & Gas Development Company Limited", "exchange": "PSX"},
    {"ticker": "ENGRO", "name": "Engro Corporation", "exchange": "PSX"},
    {"ticker": "LUCK", "name": "Lucky Cement Limited", "exchange": "PSX"},
    {"ticker": "HBL", "name": "Habib Bank Limited", "exchange": "PSX"},
    {"ticker": "UBL", "name": "United Bank Limited", "exchange": "PSX"},
    {"ticker": "MCB", "name": "MCB Bank Limited", "exchange": "PSX"},
    {"ticker": "PPL", "name": "Pakistan Petroleum Limited", "exchange": "PSX"},
    {"ticker": "FFC", "name": "Fauji Fertilizer Company", "exchange": "PSX"},
    {"ticker": "EFERT", "name": "Engro Fertilizers Limited", "exchange": "PSX"},
    {"ticker": "HUBC", "name": "The Hub Power Company", "exchange": "PSX"},
    {"ticker": "PSO", "name": "Pakistan State Oil", "exchange": "PSX"},
    {"ticker": "MEBL", "name": "Meezan Bank Limited", "exchange": "PSX"},
    {"ticker": "SYS", "name": "Systems Limited", "exchange": "PSX"},
    {"ticker": "TRG", "name": "TRG Pakistan Limited", "exchange": "PSX"},
    {"ticker": "BAFL", "name": "Bank Alfalah Limited", "exchange": "PSX"},
    {"ticker": "MTL", "name": "Millat Tractors Limited", "exchange": "PSX"},
    {"ticker": "MARI", "name": "Mari Petroleum Company", "exchange": "PSX"},
    {"ticker": "POL", "name": "Pakistan Oilfields Limited", "exchange": "PSX"},
    {"ticker": "PTC", "name": "Pakistan Telecommunication", "exchange": "PSX"},
    {"ticker": "FFBL", "name": "Fauji Fertilizer Bin Qasim", "exchange": "PSX"},
    {"ticker": "NESTLE", "name": "Nestle Pakistan Limited", "exchange": "PSX"},
    {"ticker": "COLG", "name": "Colgate Palmolive Pakistan", "exchange": "PSX"},
    {"ticker": "NBP", "name": "National Bank of Pakistan", "exchange": "PSX"},
    {"ticker": "ATRL", "name": "Attock Refinery Limited", "exchange": "PSX"},
    {"ticker": "LCI", "name": "Lucky Core Industries", "exchange": "PSX"},
    {"ticker": "GHNI", "name": "Ghandhara Industries", "exchange": "PSX"},
    {"ticker": "FABL", "name": "Faysal Bank Limited", "exchange": "PSX"},
    {"ticker": "AKBL", "name": "Askari Bank Limited", "exchange": "PSX"},
    {"ticker": "KSE100", "name": "KSE-100 Index", "exchange": "PSX", "m": "IDX"},
    {"ticker": "KSE30", "name": "KSE-30 Index", "exchange": "PSX", "m": "IDX"},
    {"ticker": "KMI30", "name": "KMI-30 Index", "exchange": "PSX", "m": "IDX"},
    {"ticker": "ALLSHR", "name": "All Share Index", "exchange": "PSX", "m": "IDX"},
]

KNOWN_INDEX_SYMBOLS: tuple[str, ...] = ("KSE100", "KSE30", "KMI30", "ALLSHR", "MZNPI")


def fallback_symbol_rows() -> list[dict[str, Any]]:
    return [dict(row) for row in PSX_SYMBOL_UNIVERSE]
