"""Main entry point for Call Me Maybe constrained function calling."""

import argparse
import json
import os
import sys
from typing import Any, Dict, List

from pydantic import ValidationError

from src.decoder import ConstrainedDecoder


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Call Me Maybe - Constrained Function Calling"
    )
    parser.add_argument(
        "--functions_definition",
        type=str,
        default="data/input/functions_definition.json",
        help="Path to functions definition JSON file",
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/input/function_calling_tests.json",
        help="Path to input test prompts JSON file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/output/function_calls.json",
        help="Path to output JSON file",
    )
    return parser.parse_args()


def main() -> None:
    """Run constrained decoding pipeline over input test prompts."""
    args = parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            test_prompts: List[Dict[str, Any]] = json.load(f)

        decoder = ConstrainedDecoder(args.functions_definition)

        results: List[Dict[str, Any]] = []
        for item in test_prompts:
            prompt = item.get("prompt", "")
            if not prompt:
                continue
            prediction = decoder.predict(prompt)
            results.append(prediction.model_dump())

        output_dir = os.path.dirname(args.output)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"Success: {len(results)} calls saved to '{args.output}'.")

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        KeyError,
        OSError,
        ValidationError,
    ) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
