from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from .schema import SOPConfig


class SOPMutation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_path: str
    current_value: Any
    proposed_value: Any
    rationale: str

    @model_validator(mode="after")
    def validate_field_path(self) -> SOPMutation:
        _validate_field_path_exists(SOPConfig, self.field_path)
        return self


def _validate_field_path_exists(model: type[BaseModel], field_path: str) -> None:
    """Validate dot-notation field_path against a Pydantic model type."""

    parts = [p for p in field_path.split(".") if p]
    if not parts:
        raise ValueError("field_path must be non-empty")

    current_model: type[BaseModel] = model
    for i, part in enumerate(parts):
        fields = getattr(current_model, "model_fields", {})
        if part not in fields:
            raise ValueError(
                f"Invalid field_path segment '{part}' at position {i} for model {current_model.__name__}"
            )

        annotation = fields[part].annotation
        origin = getattr(annotation, "__origin__", None)

        # Optional[T] / Union[T, None] -> pick first non-None
        if origin is None and getattr(annotation, "__args__", None):
            args = [a for a in annotation.__args__ if a is not type(None)]  # noqa: E721
            if len(args) == 1:
                annotation = args[0]

        if i < len(parts) - 1:
            if isinstance(annotation, type) and issubclass(annotation, BaseModel):
                current_model = annotation
            else:
                raise ValueError(
                    f"field_path '{field_path}' attempts to traverse into non-model field '{part}'"
                )
