"""The structured error envelope every non-2xx response uses
(docs/03-ARCHITECTURE.md #27, docs/02-PRD.md #30): predictable, never a
raw stack trace.
"""

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    type: str
    message: str
    details: dict[str, object] = {}


class ErrorEnvelope(BaseModel):
    error: ErrorDetail
