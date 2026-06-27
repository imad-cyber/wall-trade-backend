"""Map Capital Stake API responses to domain models."""
from app.domain.company.models import CompanyProfile


class CompanyMapper:
    @staticmethod
    def to_domain(ticker: str, raw: dict) -> CompanyProfile:
        return CompanyProfile.from_provider_row(ticker, raw)
