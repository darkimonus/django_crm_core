from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class Result:
    """
    Outcome of an SCD2 upsert operation.

    Attributes:
        instance: The ORM instance resulting from the operation (the new
                  current row for created/updated, or the unchanged current
                  row for noop).
        status: Operation result: "created", "updated", or "noop".
    """
    instance: Any
    status: Literal["created", "updated", "noop"]
