"""
SCD2 upsert service facade for CRM entities and details.

Provides transactional upserts that implement close-and-open versioning and
return a lightweight `Result` with the instance and status.
"""

from .types import Result
from .entity import upsert_entity
from .detail import upsert_entity_detail

__all__ = [
    "Result",
    "upsert_entity",
    "upsert_entity_detail",
]
