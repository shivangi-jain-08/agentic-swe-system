from __future__ import annotations

from pathlib import Path
from typing import Any

import semver
import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RetryLimits(BaseModel):
    model_config = ConfigDict(extra="forbid")

    developer: int = 2
    loop: int = 3


class StopConditions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_subtasks: int = 5
    qa_pass_threshold: float = 0.8


class FeatureFlags(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_product_analyst: bool = True
    use_tech_lead: bool = True


class ToolPermissions(BaseModel):
    """Optional SOP section used by the roadmap to make permissions explicit."""

    model_config = ConfigDict(extra="forbid")

    developer: list[str] = Field(default_factory=lambda: ["read_file", "write_diff"])
    reviewer: list[str] = Field(default_factory=lambda: ["read_diff"])
    qa: list[str] = Field(default_factory=lambda: ["run_pytest", "run_pylint", "run_radon"])


class ModelAssignments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    developer: str = "deepseek-coder:6.7b"
    reviewer: str = "deepseek-coder:6.7b"
    tech_lead: str = "qwen2.5-coder:7b"
    product_analyst: str = "qwen2.5-coder:7b"
    diagnostic: str | None = "llama3.2:3b"
    architect: str | None = "llama3.2:3b"
    qa: str | None = None  # deterministic only


class SOPConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str  # semver, e.g. "1.0.0"
    agent_order: list[str]

    model_assignments: ModelAssignments = Field(default_factory=ModelAssignments)
    tool_permissions: ToolPermissions | None = None

    retry_limits: RetryLimits = Field(default_factory=RetryLimits)
    stop_conditions: StopConditions = Field(default_factory=StopConditions)
    feature_flags: FeatureFlags = Field(default_factory=FeatureFlags)

    @field_validator("version")
    @classmethod
    def _validate_semver(cls, v: str) -> str:
        semver.Version.parse(v)
        return v

    @classmethod
    def from_yaml(cls, path: str | Path) -> SOPConfig:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return cls.model_validate(data)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()
