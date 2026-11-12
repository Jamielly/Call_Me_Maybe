# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    makefile                                           :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: jamsilva <jamsilva@student.42.fr>          +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/11/12 09:54:50 by jamsilva          #+#    #+#              #
#    Updated: 2026/11/12 13:33:07 by jamsilva         ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

all: run

install:
			uv sync

run:
			uv run python -m src --functions\_definition data/input/functions\_definition.json --input data/input/function\_calling\_tests.json --output data/output/function\_calls.json
debug:
			uv run python -m pdb -m src ...

lint: 
			uv run flake8 .
			uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
			
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


.PHONY: all install run debug clean fclean lint lint-strict