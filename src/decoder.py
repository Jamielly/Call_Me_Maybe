"""Constrained decoding engine integrated with Pydantic models."""

import json
from typing import Dict, List

from llm_sdk.small_llm_model import Small_LLM_Model
from src.models import FunctionCallOutput, FunctionDefinition, ParamValue


class ConstrainedDecoder:
    """Constrained decoding engine for 42 Call Me Maybe."""

    def __init__(self, functions_def_path: str) -> None:
        with open(functions_def_path, "r", encoding="utf-8") as f:
            raw_functions = json.load(f)

        self.functions: List[FunctionDefinition] = [
            FunctionDefinition(**fn) for fn in raw_functions
        ]
        self.functions_by_name: Dict[str, FunctionDefinition] = {
            fn.name: fn for fn in self.functions
        }

        self.model = Small_LLM_Model()
        self.vocab: Dict[int, str] = self._load_vocab()
        self.string_tokens = self._get_string_tokens()
        self.number_tokens = self._get_number_tokens(allow_float=True)
        self.integer_tokens = self._get_number_tokens(allow_float=False)

    def _load_vocab(self) -> Dict[int, str]:
        """Load token ID to string mapping from model vocabulary."""
        vocab_path = self.model.get_path_to_vocab_file()
        with open(vocab_path, "r", encoding="utf-8") as f:
            raw_vocab = json.load(f)
        if isinstance(next(iter(raw_vocab.keys())), str):
            return {int(v): k for k, v in raw_vocab.items()}
        return {int(k): v for k, v in raw_vocab.items()}

    def _encode_clean(self, text: str) -> List[int]:
        """Encode text filtering out Qwen special tokens."""
        return [t for t in self.model.encode(text) if t < 151643]

    def _get_string_tokens(self) -> List[int]:
        """Filter safe tokens for JSON string values."""
        allowed: List[int] = []
        for tid in self.vocab:
            if tid >= 151643:
                continue
            decoded = self.model.decode([tid])
            if any(ch in decoded for ch in ("\n", "\r", "\\")):
                continue
            if '"' in decoded and decoded != '"':
                continue
            allowed.append(tid)
        return allowed

    def _get_number_tokens(self, allow_float: bool) -> List[int]:
        """Filter tokens containing only digits, minus sign, or dot."""
        valid_chars = set("0123456789-")
        if allow_float:
            valid_chars.add(".")

        allowed: List[int] = []
        for tid in self.vocab:
            if tid >= 151643:
                continue
            decoded = self.model.decode([tid])
            if decoded and all(c in valid_chars for c in decoded):
                allowed.append(tid)
        return allowed

    def predict_function_name(self, user_prompt: str) -> str:
        """Select function name using token-by-token prefix tree."""
        summary = "\n".join(
            f"- {fn.name}: {fn.description}" for fn in self.functions
        )
        prompt_text = (
            "Given the user request, identify the best function to call.\n"
            f"Available functions:\n{summary}\n\n"
            f'User request: "{user_prompt}"\n'
            "Selected function name:"
        )
        current_ids = self._encode_clean(prompt_text)
        candidates: Dict[str, List[int]] = {
            fn.name: self._encode_clean(f" {fn.name}") for fn in self.functions
        }

        step = 0
        while len(candidates) > 1:
            logits = self.model.get_logits_from_input_ids(current_ids)
            next_tokens = {
                toks[step] for toks in candidates.values() if step < len(toks)
            }
            if not next_tokens:
                break

            best_token = max(next_tokens, key=lambda t: logits[t])
            current_ids.append(best_token)
            candidates = {
                name: toks
                for name, toks in candidates.items()
                if step < len(toks) and toks[step] == best_token
            }
            step += 1

        return next(iter(candidates.keys()))

    def _generate_string_value(self, current_ids: List[int]) -> str:
        """Generate JSON string value until closing quote is chosen."""
        current_ids.extend(self._encode_clean('"'))
        generated: List[int] = []

        for _ in range(100):
            logits = self.model.get_logits_from_input_ids(current_ids)
            best_token = max(self.string_tokens, key=lambda t: logits[t])
            current_ids.append(best_token)
            if self.model.decode([best_token]) == '"':
                break
            generated.append(best_token)

        return self.model.decode(generated)

    def _generate_number_value(
        self, current_ids: List[int], is_float: bool
    ) -> ParamValue:
        """Generate valid int or float until delimiter token is chosen."""
        allowed = self.number_tokens if is_float else self.integer_tokens
        delimiters = self._encode_clean(",") + self._encode_clean("}")
        raw_num = ""

        for step in range(20):
            logits = self.model.get_logits_from_input_ids(current_ids)
            pool = allowed if step == 0 else allowed + delimiters
            best_token = max(pool, key=lambda t: logits[t])

            if best_token in delimiters:
                break

            decoded = self.model.decode([best_token])
            if "." in decoded and ("." in raw_num or not is_float):
                break
            if "-" in decoded and len(raw_num) > 0:
                break

            raw_num += decoded
            current_ids.append(best_token)

        if not raw_num or raw_num in ("-", ".", "-."):
            return 0.0 if is_float else 0
        return float(raw_num) if is_float else int(raw_num)

    def _generate_boolean_value(self, current_ids: List[int]) -> bool:
        """Force strict choice between true and false tokens."""
        options = {
            True: self._encode_clean("true"),
            False: self._encode_clean("false"),
        }
        logits = self.model.get_logits_from_input_ids(current_ids)
        best_bool = max(options.keys(), key=lambda b: logits[options[b][0]])
        current_ids.extend(options[best_bool])
        return best_bool

    def predict(self, user_prompt: str) -> FunctionCallOutput:
        """Run full constrained decoding pipeline and return typed output."""
        fn_name = self.predict_function_name(user_prompt)
        fn_def = self.functions_by_name[fn_name]

        context_text = (
            f'User request: "{user_prompt}"\n'
            f"Function: {fn_name}\n"
            f"Description: {fn_def.description}\n"
            "Arguments JSON:\n{"
        )
        current_ids = self._encode_clean(context_text)
        extracted: Dict[str, ParamValue] = {}

        items = list(fn_def.parameters.items())
        for idx, (param_name, schema) in enumerate(items):
            current_ids.extend(self._encode_clean(f'"{param_name}": '))

            if schema.type == "integer":
                val: ParamValue = self._generate_number_value(
                    current_ids, is_float=False
                )
            elif schema.type == "number":
                val = self._generate_number_value(current_ids, is_float=True)
            elif schema.type == "boolean":
                val = self._generate_boolean_value(current_ids)
            else:
                val = self._generate_string_value(current_ids)

            extracted[param_name] = val
            sep = ", " if idx < len(items) - 1 else "}"
            current_ids.extend(self._encode_clean(sep))

        if not items:
            current_ids.extend(self._encode_clean("}"))

        result = FunctionCallOutput(
            prompt=user_prompt,
            name=fn_name,
            parameters=extracted,
        )
        result.normalize(fn_def)
        return result
