"""Market feel repository."""
from app.repositories.base import BaseRepository


class MarketFeelRepository(BaseRepository):
    def __init__(self, db_client):
        super().__init__(db_client, "market_feel")
