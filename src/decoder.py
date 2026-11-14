import json
from typing import Any, Dict, List
from llm_sdk.small_llm_model import Small_LLM_Model


class ConstrainedDecoder:
    def __init__(self, functions_def_path: str) -> None:
        # 1. Lê o arquivo JSON com as definições das funções
        with open(functions_def_path, "r", encoding="utf-8") as f:
            self.functions: List[Dict[str, Any]] = json.load(f)

        # 2. Inicia o modelo da 42
        self.model = Small_LLM_Model()

        # 3. Cria um dicionário rápido para achar uma função pelo nome depois
        self.functions_by_name: Dict[str, Dict[str, Any]] = {
            fn["name"]: fn for fn in self.functions
        }
