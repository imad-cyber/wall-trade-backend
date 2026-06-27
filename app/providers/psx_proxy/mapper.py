"""Map PSX Proxy responses to domain models."""
from app.domain.market.models import Price


class PriceMapper:
    @staticmethod
    def to_domain(raw: dict) -> Price:
        return Price.from_provider_row(raw)

    @staticmethod
    def to_domain_list(raw_list: list[dict]) -> list[Price]:
        return [PriceMapper.to_domain(item) for item in raw_list]
