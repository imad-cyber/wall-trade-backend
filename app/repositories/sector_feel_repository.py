"""Sector feel repository."""
from app.repositories.base import BaseRepository


class SectorFeelRepository(BaseRepository):
    def __init__(self, db_client):
        super().__init__(db_client, "sector_feel")
