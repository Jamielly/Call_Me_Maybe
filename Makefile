# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    Makefile                                           :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: jamsilva <jamsilva@student.42.fr>          +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/11/12 09:54:50 by jamsilva          #+#    #+#              #
#    Updated: 2026/11/18 12:35:22 by jamsilva         ###   ########.fr        #
#                                                                              #
# **************************************************************************** #


ARGS = --functions_definition data/input/functions_definition.json \
	--input data/input/function_calling_tests.json \
	--output data/output/function_calling_results.json

MYPY_FLAGS = --warn-return-any --warn-unused-ignores --ignore-missing-imports \
	--disallow-untyped-defs --check-untyped-defs

export UV_CACHE_DIR = $(CURDIR)/.cache/uv
export HF_HOME = $(CURDIR)/.cache/huggingface
export UV_LINK_MODE = copy

all: install run

install:
			uv sync
			uv pip install -e ./llm_sdk

run:
			uv run python -m src $(ARGS)
debug:
			uv run python -m pdb -m src $(ARGS)

lint: 
			uv run flake8 .
			uv run mypy . $(MYPY_FLAGS)
			
lint-strict:
			uv run flake8 .
			uv run mypy . --strict

clean:
			find . -type d -name "__pycache__" -exec rm -rf {} +
			find . -type d -name ".mypy_cache" -exec rm -rf {} +
			find . -type d -name ".pytest_cache" -exec rm -rf {} +
			find . -type f -name "*.pyc" -delete
			rm -rf data/output/

fclean: clean
	rm -rf data/output/ .venv

re:	fclean all

.PHONY: all install run debug clean fclean re lint lint-strict
