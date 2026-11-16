import json
from typing import Any, Dict, List
from llm_sdk.small_llm_model import Small_LLM_Model


class ConstrainedDecoder:
    """Motor de Decodificação Restrita para Function Calling (42 Call Me Maybe)."""

    def __init__(self, functions_def_path: str) -> None:
        with open(functions_def_path, "r", encoding="utf-8") as f:
            self.functions: List[Dict[str, Any]] = json.load(f)

        self.model = Small_LLM_Model()
        self.functions_by_name: Dict[str, Dict[str, Any]] = {
            fn["name"]: fn for fn in self.functions
        }

        # Pré-carrega o vocabulário para filtrar tokens válidos por tipo de dado
        self.vocab: Dict[int, str] = self._load_vocab()
        self.string_allowed_tokens = self._get_string_tokens()
        self.number_allowed_tokens = self._get_number_tokens(allow_float=True)
        self.integer_allowed_tokens = self._get_number_tokens(allow_float=False)

    def _load_vocab(self) -> Dict[int, str]:
        """Carrega o mapeamento ID -> texto do tokenizador do modelo."""
        vocab_path = self.model.get_path_to_vocab_file()
        with open(vocab_path, "r", encoding="utf-8") as f:
            raw_vocab = json.load(f)
        # Inverte se estiver no formato {token: id}
        if isinstance(next(iter(raw_vocab.keys())), str):
            return {int(v): k for k, v in raw_vocab.items()}
        return {int(k): v for k, v in raw_vocab.items()}

    def _encode_clean(self, text: str) -> List[int]:
        """Codifica texto garantindo que não haja tokens especiais de início/fim."""
        tokens = self.model.encode(text)
        # Remove possíveis tokens especiais do Qwen (IDs >= 151643)
        return [t for t in tokens if t < 151643]

    def _get_string_tokens(self) -> List[int]:
        """Filtra tokens seguros para preencher valores de string em JSON."""
        allowed = []
        for tid, token_str in self.vocab.items():
            if tid >= 151643:  # Ignora tokens especiais
                continue
            decoded = self.model.decode([tid])
            # Bloqueia caracteres que quebram a string JSON sem escape
            if "\n" in decoded or "\r" in decoded or "\\" in decoded:
                continue
            # Permite aspas apenas se for o token exato de fechamento '"'
            if '"' in decoded and decoded != '"':
                continue
            allowed.append(tid)
        return allowed

    def _get_number_tokens(self, allow_float: bool) -> List[int]:
        """Filtra tokens que contêm apenas dígitos, sinal negativo ou ponto."""
        valid_chars = set("0123456789-")
        if allow_float:
            valid_chars.add(".")

        allowed = []
        for tid in self.vocab:
            if tid >= 151643:
                continue
            decoded = self.model.decode([tid])
            if decoded and all(c in valid_chars for c in decoded):
                allowed.append(tid)
        return allowed

    def predict_function_name(self, user_prompt: str) -> str:
        """Escolhe o nome da função usando árvore de prefixos token a token."""
        functions_summary = "\n".join(
            f"- {fn['name']}: {fn.get('description', '')}"
            for fn in self.functions
        )
        prompt_text = (
            f"Given the user request, identify the single best function to call.\n"
            f"Available functions:\n{functions_summary}\n\n"
            f"User request: \"{user_prompt}\"\n"
            f"Selected function name: "
        )

        current_ids = self._encode_clean(prompt_text)
        candidates = {
            fn["name"]: self._encode_clean(fn["name"])
            for fn in self.functions
        }

        step = 0
        while len(candidates) > 1:
            logits = self.model.get_logits_from_input_ids(current_ids)
            next_tokens = {
                tokens[step] for tokens in candidates.values() if step < len(tokens)
            }
            if not next_tokens:
                break

            best_token = max(next_tokens, key=lambda t: logits[t])
            current_ids.append(best_token)

            candidates = {
                name: tokens
                for name, tokens in candidates.items()
                if step < len(tokens) and tokens[step] == best_token
            }
            step += 1

        return next(iter(candidates.keys()))

    def _generate_string_value(self, current_ids: List[int]) -> str:
        """Gera o conteúdo de uma string JSON até o modelo escolher fechar aspas."""
        current_ids.extend(self._encode_clean('"'))
        generated_tokens: List[int] = []

        for _ in range(100):  # Limite de segurança para evitar loop infinito
            logits = self.model.get_logits_from_input_ids(current_ids)
            best_token = max(self.string_allowed_tokens, key=lambda t: logits[t])
            decoded = self.model.decode([best_token])

            current_ids.append(best_token)
            if decoded == '"':
                break
            generated_tokens.append(best_token)

        return self.model.decode(generated_tokens)

    def _generate_number_value(
        self, current_ids: List[int], is_float: bool
    ) -> int | float:
        """Gera um número válido e para quando o próximo melhor token não for numérico."""
        allowed = (
            self.number_allowed_tokens if is_float else self.integer_allowed_tokens
        )
        delimiter_tokens = self._encode_clean(",") + self._encode_clean("}")
        generated_str = ""

        for step in range(20):
            logits = self.model.get_logits_from_input_ids(current_ids)
            # No primeiro passo, força um dígito/sinal; nos seguintes, permite encerrar
            candidates = allowed if step == 0 else allowed + delimiter_tokens
            best_token = max(candidates, key=lambda t: logits[t])

            if best_token in delimiter_tokens:
                break

            decoded = self.model.decode([best_token])
            # Evita múltiplos pontos decimais ou sinal negativo no meio do número
            if "." in decoded and ("." in generated_str or not is_float):
                break
            if "-" in decoded and len(generated_str) > 0:
                break

            generated_str += decoded
            current_ids.append(best_token)

        if not generated_str or generated_str in ("-", ".", "-."):
            return 0.0 if is_float else 0
        return float(generated_str) if is_float else int(generated_str)

    def _generate_boolean_value(self, current_ids: List[int]) -> bool:
        """Força a escolha estrita entre 'true' e 'false'."""
        options = {
            True: self._encode_clean("true"),
            False: self._encode_clean("false"),
        }
        logits = self.model.get_logits_from_input_ids(current_ids)
        best_bool = max(options.keys(), key=lambda b: logits[options[b][0]])
        current_ids.extend(options[best_bool])
        return best_bool

    def predict(self, user_prompt: str) -> Dict[str, Any]:
        """Executa o pipeline completo e retorna o dicionário pronto para serializar."""
        fn_name = self.predict_function_name(user_prompt)
        fn_schema = self.functions_by_name[fn_name]
        properties = fn_schema.get("parameters", {}).get("properties", {})

        # Inicia o contexto guiando o modelo a preencher o objeto JSON da função
        context_text = (
            f"User request: \"{user_prompt}\"\n"
            f"Function: {fn_name}\n"
            f"Description: {fn_schema.get('description', '')}\n"
            f"Arguments JSON:\n{{"
        )
        current_ids = self._encode_clean(context_text)
        extracted_args: Dict[str, Any] = {}

        prop_items = list(properties.items())
        for idx, (param_name, param_info) in enumerate(prop_items):
            param_type = param_info.get("type", "string")

            # Força a chave exata do parâmetro no contexto (ex: '"city": ')
            key_prefix = f'"{param_name}": '
            current_ids.extend(self._encode_clean(key_prefix))

            # Decodifica o valor respeitando a restrição de tipo do schema
            if param_type == "string":
                val = self._generate_string_value(current_ids)
            elif param_type == "integer":
                val = self._generate_number_value(current_ids, is_float=False)
            elif param_type == "number":
                val = self._generate_number_value(current_ids, is_float=True)
            elif param_type == "boolean":
                val = self._generate_boolean_value(current_ids)
            else:
                val = self._generate_string_value(current_ids)

            extracted_args[param_name] = val

            # Adiciona vírgula entre parâmetros ou fecha o objeto JSON
            if idx < len(prop_items) - 1:
                current_ids.extend(self._encode_clean(", "))
            else:
                current_ids.extend(self._encode_clean("}"))

        if not prop_items:
            current_ids.extend(self._encode_clean("}"))

        return {
            "prompt": user_prompt,
            "fn_name": fn_name,
            "args": extracted_args,
        }
