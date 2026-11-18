import argparse
import json
import os
import sys
from typing import Any, Dict, List

from src.decoder import ConstrainedDecoder


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Call Me Maybe - Function Calling"
    )
    parser.add_argument(
        "--functions_definition",
        default="data/input/functions_definition.json",
        help="Path to functions definition JSON file",
    )
    parser.add_argument(
        "--input",
        default="data/input/function_calling_tests.json",
        help="Path to input test queries JSON file",
    )
    parser.add_argument(
        "--output",
        default="data/output/function_calling_results.json",
        help="Path to output JSON file",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    green = "\033[92m"
    red = "\033[91m"
    reset = "\033[0m"

    try:
        # 1. Carrega os prompts de teste do arquivo de entrada
        with open(args.input, "r", encoding="utf-8") as f:
            test_prompts: List[Dict[str, Any]] = json.load(f)

        # 2. Inicializa o decoder uma única vez (carrega o modelo Qwen)
        decoder = ConstrainedDecoder(args.functions_definition)

        # 3. Processa cada prompt da lista
        results: List[Dict[str, Any]] = []
        for item in test_prompts:
            prompt_text = item["prompt"]
            prediction = decoder.predict(prompt_text)
            results.append(prediction)

        # 4. Garante que o diretório de saída existe (caso passem só o nome do arquivo)
        output_dir = os.path.dirname(args.output)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # 5. Salva o JSON final formatado
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"{green}Call Me Maybe finalizado com sucesso!{reset}")
        print(f"Resultados salvos em: {args.output}")

    except (FileNotFoundError, json.JSONDecodeError, KeyError, OSError) as exc:
        print(f"{red}Erro durante a execução: {exc}{reset}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
