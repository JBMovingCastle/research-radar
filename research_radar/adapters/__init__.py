from .arxiv import ArxivAdapter
from .crossref import CrossrefAdapter
from .feeds import FeedAdapter
from .openalex import OpenAlexAdapter
from .semantic_scholar import SemanticScholarRecommendationsAdapter, SemanticScholarSearchAdapter
from .webpage import WebPageAdapter

ADAPTERS = (
    CrossrefAdapter,
    ArxivAdapter,
    SemanticScholarSearchAdapter,
    SemanticScholarRecommendationsAdapter,
    OpenAlexAdapter,
    FeedAdapter,
    WebPageAdapter,
)

__all__ = ["ADAPTERS"]
