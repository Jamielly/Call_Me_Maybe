*This project has been created as part of the 42 curriculum by jamsilva*

# Call_Me_Maybe

### 📁 1\. Estrutura de Pastas e Ambiente com `uv`

O projeto exige o gerenciador de pacotes **uv** e uma estrutura modular chamada via `python -m src`[2]:

```
call_me_maybe/
├── pyproject.toml         # Configurado via uv com dependências: pydantic, numpy
├── llm_sdk/               # Pacote fornecido pela 42 (Small_LLM_Model)
├── data/
│   ├── input/
│   │   ├── functions_definition.json   # Funções disponíveis
│   │   └── function_calling_tests.json # Perguntas de teste
│   └── output/
│       └── function_calls.json         # Saída gerada pelo seu programa
├── src/
│   ├── __init__.py
│   ├── __main__.py        # Ponto de entrada CLI (argparse)
│   ├── models.py          # Modelos Pydantic para validação das definições e saídas
│   └── decoder.py         # Lógica da LLM e Constrained Decoding
└── README.md              # Requisitos padrão da 42
```