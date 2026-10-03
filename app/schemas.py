"""Validated HTTP contracts for the local MVP."""

from datetime import datetime
from math import isfinite
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjectCreate(StrictModel):
    name: str = Field(max_length=100)
    description: str = Field(default="", max_length=1_000)

    @field_validator("name")
    @classmethod
    def trim_nonblank_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be blank")
        return value


class Project(ProjectCreate):
    id: str
    created_at: datetime


class ProjectList(StrictModel):
    items: list[Project]


class Expectation(StrictModel):
    expected_answer: str = Field(max_length=10_000)
    expected_tools: list[str] | None = None
    prohibited_text: list[str] = Field(default_factory=list)
    max_latency_ms: float | None = Field(default=None, ge=0)
    max_total_tokens: Annotated[int, Field(strict=True, ge=0)] | None = None

    @field_validator("expected_answer")
    @classmethod
    def trim_expected_answer(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("expected_answer must not be blank")
        return value

    @field_validator("expected_tools")
    @classmethod
    def validate_tool_names(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned = [name.strip() for name in value]
        if any(not name for name in cleaned):
            raise ValueError("tool names must not be blank")
        return cleaned

    @field_validator("prohibited_text")
    @classmethod
    def validate_prohibited_text(cls, value: list[str]) -> list[str]:
        cleaned = [phrase.strip() for phrase in value]
        if any(not phrase for phrase in cleaned):
            raise ValueError("prohibited phrases must not be blank")
        return cleaned

    @field_validator("max_latency_ms", mode="before")
    @classmethod
    def reject_invalid_latency(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("max_latency_ms must be a number")
        if isinstance(value, (int, float)) and not isfinite(value):
            raise ValueError("max_latency_ms must be finite")
        return value


MockScenario = Literal[
    "pass",
    "wrong_answer",
    "unexpected_tool",
    "prohibited_output",
    "slow",
    "over_tokens",
    "missing_metric",
    "invalid_schema",
    "error",
]


class CaseCreate(StrictModel):
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", min_length=1, max_length=80)
    name: str = Field(max_length=100)
    input: str = Field(max_length=10_000)
    expectation: Expectation
    mock_scenario: MockScenario

    @field_validator("name", "input")
    @classmethod
    def trim_nonblank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value

    @model_validator(mode="after")
    def validate_scenario_requirements(self) -> "CaseCreate":
        expectation = self.expectation
        if self.mock_scenario == "prohibited_output" and not expectation.prohibited_text:
            raise ValueError("prohibited_output requires prohibited_text")
        if self.mock_scenario == "slow" and expectation.max_latency_ms is None:
            raise ValueError("slow requires max_latency_ms")
        if self.mock_scenario == "over_tokens" and expectation.max_total_tokens is None:
            raise ValueError("over_tokens requires max_total_tokens")
        return self


class TestCase(CaseCreate):
    id: str
    project_id: str
    created_at: datetime


class CaseList(StrictModel):
    items: list[TestCase]

