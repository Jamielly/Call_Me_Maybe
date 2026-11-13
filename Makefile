# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    Makefile                                           :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: jamsilva <jamsilva@student.42.fr>          +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/11/12 09:54:50 by jamsilva          #+#    #+#              #
#    Updated: 2026/11/13 09:28:02 by jamsilva         ###   ########.fr        #
#                                                                              #
# **************************************************************************** #


ARGS = --functions_definition data/input/functions_definition.json \
			--input data/input/functions_calling_tests.json \
			--output data/output/functions_calls.json

MYPY_FLAGS = --warn-return-any --warn-unused-ignores --ignore-missing-imports \
 --disallow-untyped-defs --check-untyped-defs

all: run

install:
			uv sync

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

fclean:
	rm -rf data/output/ .venv

re:	fclean all

.PHONY: all install run debug clean fclean re lint lint-strict