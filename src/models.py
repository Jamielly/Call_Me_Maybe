"""Data models for function definitions and call outputs."""

from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

ParamValue = Union[str, int, float, bool]


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


class FunctionCallOutput(BaseModel):
    """Model for the final output written to function_calls.json."""

    prompt: str
    name: str
    parameters: dict[str, ParamValue] = Field(default_factory=dict)

    def normalize(self, func_def: FunctionDefinition) -> None:
        """Ensure number parameters are float and integer are int."""
        for key, schema in func_def.parameters.items():
            if key in self.parameters:
                if schema.type == "number":
                    self.parameters[key] = float(self.parameters[key])
                elif schema.type == "integer":
                    self.parameters[key] = int(float(self.parameters[key]))
