"""Data models for function definitions, prompts, and call outputs."""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ParameterSchema(BaseModel):
    """Schema for an individual parameter required by a function."""

    model_config = ConfigDict(extra="ignore")

    type: str
    description: Optional[str] = None


class FunctionDefinition(BaseModel):
    """Model representing each function in functions_definition.json."""

    model_config = ConfigDict(extra="ignore")

    name: str
    description: str
    parameters: dict[str, ParameterSchema] = Field(default_factory=dict)
    returns: Optional[Any] = None


class PromptInput(BaseModel):
    """Model representing each input prompt from function_calling_tests.json."""

    model_config = ConfigDict(extra="ignore")

    prompt: str


class FunctionCallOutput(BaseModel):
    """Model for the final output written to function_calls.json."""

    prompt: str
    name: str
    parameters: dict[str, Any] = Field(default_factory=dict)
