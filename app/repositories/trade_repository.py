"""Trade repository."""
from app.repositories.base import BaseRepository


class TradeRepository(BaseRepository):
    def __init__(self, db_client):
        super().__init__(db_client, "user_trades")
