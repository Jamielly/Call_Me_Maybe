*This project has been created as part of the 42 curriculum by jamsilva.*

# Call Me Maybe

<div align="center">

<img src="assets/call_me_maybe.gif" alt="Constrained decoding: JSON is built token by token while invalid candidates are masked out" width="720"/>

<sub>Illustrative representation of constrained decoding: invalid tokens are masked by type, and the highest-logit valid token is chosen at each free step.</sub>

</div>

A deterministic, type-safe function calling engine written in Python. It turns natural language prompts into structured, machine-executable JSON function calls, using constrained decoding over a local Small Language Model (`Qwen/Qwen3-0.6B`).

## Description

Small Language Models (SLMs) can understand what a user wants, but when they generate freely they often produce invalid JSON or values that break the parameter schema.

**Call Me Maybe** closes that gap without external structured-generation libraries such as Outlines, Guidance or the Hugging Face `transformers` generation pipeline. It reads the raw next-token logits and the vocabulary exposed by `llm_sdk`, and enforces structural and type constraints at every decoding step:

- **Valid JSON by construction:** structural tokens (`{`, `}`, `:`, `,`, `"`) and the exact schema keys are inserted deterministically, not sampled.
- **Prefix-tree function selection:** candidate function names are resolved token by token against valid vocabulary prefixes, so the model cannot pick a name that does not exist or a partial match of a similar name.
- **Strict type enforcement:** the allowed token pool is filtered per parameter type (`string`, `integer`, `number`, `boolean`), and the values are normalized with Pydantic models. `number` values stay `float` in the output.

## Instructions

### Prerequisites

- Python 3.10 or higher
- [`uv`](https://docs.astral.sh/uv/), for dependency and environment management

### Installation

```bash
git clone <repository-url>
cd call_me_maybe
uv sync
```

### Execution

Run with the default input and output paths:

```bash
uv run python -m src
```

Or pass custom paths:

```bash
uv run python -m src \
  --functions_definition data/input/functions_definition.json \
  --input data/input/function_calling_tests.json \
  --output data/output/function_calls.json
```

### Lint and type-check

Check PEP 8 compliance and strict static typing, as required by the 42 norm:

```bash
uv run flake8 src
uv run mypy --strict src
```

## Project Structure

```text
call_me_maybe/
├── Makefile
├── pyproject.toml
├── README.md
├── llm_sdk/
│   └── small_llm_model.py
├── data/
│   ├── input/
│   │   ├── functions_definition.json
│   │   └── function_calling_tests.json
│   └── output/
│       └── function_calls.json
└── src/
    ├── __init__.py
    ├── __main__.py
    ├── decoder.py
    ├── main.py
    └── models.py
```

## Algorithm: Constrained Decoding

The engine works in three stages, all driven by the model's logits.

**1. Vocabulary pre-filtering (`ConstrainedDecoder`).** At initialization, the tokenizer vocabulary is split into safe subsets: strings exclude unescaped newlines, backslashes and premature quotes; integers use only the digits and `-`; numbers also allow `.`. Special control tokens are masked out.

**2. Prefix-tree routing (`predict_function_name`).** Scoring only the first token of each function name is not enough, because several names share prefixes. The decoder advances one token at a time, keeping only the candidates whose prefix matches what has been generated so far, and picks the highest-logit token among the remaining valid candidates until a single function is uniquely determined.

**3. Schema-guided JSON construction (`predict`).** Once the function is chosen, the decoder walks its Pydantic `FunctionDefinition` parameters. For each one it appends the exact JSON key to the context, then samples the highest-logit token inside that parameter's allowed pool.

Token masking is what keeps the output valid: a token outside the allowed pool gets no probability, no matter how high the model scored it.

## Design Decisions

- **No constrained-decoding library.** Writing the logit masking by hand makes every rule explicit and testable, and keeps the dependency list small.
- **Structure is deterministic, values are sampled.** Keys, delimiters and braces never depend on the model's sampling, which removes the most common source of broken JSON from small models.
- **Type normalization after decoding.** Values are cast by the Pydantic models (`integer` to `int`, `number` to `float`), so the output matches the evaluation schema exactly.
- **Explicit prefix tree over greedy first-token scoring.** Function names that share prefixes are resolved correctly, instead of relying on the first token alone.

## Resources

### Technical references

- [Qwen/Qwen3-0.6B on Hugging Face](https://huggingface.co/Qwen/Qwen3-0.6B): the model and tokenizer used by the engine.
- [Qwen3 Technical Report (arXiv:2505.09388)](https://arxiv.org/abs/2505.09388): background on the Qwen3 architecture and its output distribution.
- [Efficient Guided Generation for Large Language Models (Willard & Louf, arXiv:2307.09702)](https://arxiv.org/abs/2307.09702): the theory behind logit masking and finite-state constrained decoding.
- [OpenAI function calling guide](https://platform.openai.com/docs/guides/function-calling): how function calling is usually specified, using JSON schemas.
- [Pydantic documentation](https://docs.pydantic.dev/latest/): schema validation, `ConfigDict` and type coercion.
- [uv documentation](https://docs.astral.sh/uv/): dependency resolution and isolated environments.
- [mypy documentation](https://mypy.readthedocs.io/en/stable/): strict static type checking.
- [flake8 documentation](https://flake8.pycqa.org/en/latest/): PEP 8 linting.

### AI usage

In line with the 42 guidelines on AI usage, I declare the following uses of AI tools in this project:

- **Code review:** reviewing PEP 8 line-length issues reported by `flake8`.
- **Type annotations:** checking `mypy --strict` errors across the Pydantic models.
- **Documentation:** refining the clarity and structure of this README.

The core logic was written by me: constrained decoding, logit masking, vocabulary filtering and testing against the evaluation datasets. All AI suggestions were reviewed, adapted and validated before being used.
