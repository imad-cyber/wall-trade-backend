"""API v1 dependency injection — repositories, providers, and services."""
from fastapi import Depends

from app.ai.analysis_pipeline import AnalysisPipeline
from app.ai.prompt_builder import PromptBuilder
from app.dependencies import get_db_dependency
from app.providers.capital_stake.client import CapitalStakeClient
from app.providers.psx_proxy.client import PSXProxyClient
from app.providers.fmp.client import FMPClient
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.macro_repository import MacroRepository
from app.repositories.market_feel_repository import MarketFeelRepository
from app.repositories.portfolio_repository import PortfolioRepository
from app.repositories.script_history_repository import ScriptHistoryRepository
from app.repositories.sector_feel_repository import SectorFeelRepository
from app.repositories.trade_repository import TradeRepository
from app.services.analysis_service import AnalysisService
from app.services.cache_service import CacheService
from app.services.company_service import CompanyService
from app.services.macro_service import MacroService
from app.services.market_feel_service import MarketFeelService
from app.services.market_service import MarketService
from app.services.portfolio_service import PortfolioService
from app.services.script_history_service import ScriptHistoryService
from app.services.sector_feel_service import SectorFeelService
from app.services.trade_service import TradeService


def get_analysis_repo(db=Depends(get_db_dependency)) -> AnalysisRepository:
    return AnalysisRepository(db)


def get_macro_repo(db=Depends(get_db_dependency)) -> MacroRepository:
    return MacroRepository(db)


def get_portfolio_repo(db=Depends(get_db_dependency)) -> PortfolioRepository:
    return PortfolioRepository(db)


def get_trade_repo(db=Depends(get_db_dependency)) -> TradeRepository:
    return TradeRepository(db)


def get_market_feel_repo(db=Depends(get_db_dependency)) -> MarketFeelRepository:
    return MarketFeelRepository(db)


def get_sector_feel_repo(db=Depends(get_db_dependency)) -> SectorFeelRepository:
    return SectorFeelRepository(db)


def get_script_history_repo(db=Depends(get_db_dependency)) -> ScriptHistoryRepository:
    return ScriptHistoryRepository(db)


def get_capital_stake_client() -> CapitalStakeClient:
    return CapitalStakeClient()


def get_psx_client() -> PSXProxyClient:
    return PSXProxyClient()


def get_fmp_client() -> FMPClient:
    return FMPClient()


def get_cache_service(repo: AnalysisRepository = Depends(get_analysis_repo)) -> CacheService:
    return CacheService(repo)


def get_analysis_pipeline(
    capital_stake: CapitalStakeClient = Depends(get_capital_stake_client),
    macro_repo: MacroRepository = Depends(get_macro_repo),
    analysis_repo: AnalysisRepository = Depends(get_analysis_repo),
    cache_service: CacheService = Depends(get_cache_service),
) -> AnalysisPipeline:
    return AnalysisPipeline(
        capital_stake=capital_stake,
        macro_repo=macro_repo,
        analysis_repo=analysis_repo,
        cache_service=cache_service,
        prompt_builder=PromptBuilder(),
    )


def get_analysis_service(
    analysis_repo: AnalysisRepository = Depends(get_analysis_repo),
    cache_service: CacheService = Depends(get_cache_service),
    pipeline: AnalysisPipeline = Depends(get_analysis_pipeline),
) -> AnalysisService:
    return AnalysisService(analysis_repo, cache_service, pipeline)


def get_macro_service(
    macro_repo: MacroRepository = Depends(get_macro_repo),
    fmp_client: FMPClient = Depends(get_fmp_client),
) -> MacroService:
    return MacroService(macro_repo, fmp_client)


def get_company_service(
    capital_stake: CapitalStakeClient = Depends(get_capital_stake_client),
) -> CompanyService:
    return CompanyService(capital_stake)


def get_market_service(
    psx_client: PSXProxyClient = Depends(get_psx_client),
) -> MarketService:
    return MarketService(psx_client)


def get_portfolio_service(
    repo: PortfolioRepository = Depends(get_portfolio_repo),
) -> PortfolioService:
    return PortfolioService(repo)


def get_trade_service(
    repo: TradeRepository = Depends(get_trade_repo),
) -> TradeService:
    return TradeService(repo)


def get_market_feel_service(
    repo: MarketFeelRepository = Depends(get_market_feel_repo),
) -> MarketFeelService:
    return MarketFeelService(repo)


def get_sector_feel_service(
    repo: SectorFeelRepository = Depends(get_sector_feel_repo),
) -> SectorFeelService:
    return SectorFeelService(repo)


def get_script_history_service(
    repo: ScriptHistoryRepository = Depends(get_script_history_repo),
) -> ScriptHistoryService:
    return ScriptHistoryService(repo)
