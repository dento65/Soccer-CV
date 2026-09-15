"""Validated API payloads kept separate from route handlers."""
from pydantic import BaseModel, Field

class ClipPolicy(BaseModel):
    threshold: float = Field(.5, ge=0, le=1.01)
    before: float = Field(8, ge=0, le=60)
    after: float = Field(5, ge=0, le=60)
    classes: list[str] | None = None
    thresholds: dict[str, float] | None = None

class ExportRequest(BaseModel):
    clips: list[dict] = Field(min_length=1, max_length=100)

class PredictionImport(BaseModel):
    payload: dict | list
    half: int = Field(1, ge=1, le=2)
    source: str = Field('Imported action-spotting predictions', max_length=200)

class EvaluationRequest(BaseModel):
    clips: list[dict]
    references: list[dict]
