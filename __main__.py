import argparse
import os

def main() -> None:
    parser = argparse.ArgumentParser(description="Call Me Maybe - Function Calling")
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
        default="data/output/function_calls.json",
        help="Path to output JSON file",
    )
    args = parser.parse_args()

    # Garante que a pasta de saída existe
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    print("🚀 Call Me Maybe iniciado com sucesso!")
    print(f"Definições: {args.functions_definition}")
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")

if __name__ == "__main__":
    main()
