from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class Result:
    instance: Any
    status: Literal["created", "updated", "noop"]
