SHELL := /bin/bash
.ONESHELL:
.DEFAULT_GOAL := go

# ==============================================================================
# Configuration
# ==============================================================================

# Python version (override with: make PYVER=3.13)
PYVER ?= 3.11

# Virtual environment directory
VENV := .venv

# Put ~/bin first so `micromamba` is found if installed there
export PATH := $(HOME)/bin:$(PATH)

# Micromamba configuration (for Sciris / X11-xcb dependencies)
# USE_MAMBA defaults to auto:
#   - hostname contains "sciris" => use micromamba
#   - else => use venv
USE_MAMBA ?= auto
MAMBA ?= micromamba
MAMBA_ENV ?= fishx11-py$(PYVER)
MAMBA_ROOT_PREFIX ?= $(HOME)/.micromamba
export MAMBA_ROOT_PREFIX

# Auto-detect if we should use mamba based on hostname
HOSTNAME := $(shell hostname 2>/dev/null || echo unknown)
ifeq ($(USE_MAMBA),auto)
  ifneq (,$(findstring sciris,$(HOSTNAME)))
    USE_MAMBA := 1
  else
    USE_MAMBA := 0
  endif
endif

# Directories we lint/typecheck explicitly (exclude Fish/Other which is tests only)
LINT_DIRS := Fish/Admin Fish/Common Fish/Player Fish/Planning

# ==============================================================================
# Phony targets
# ==============================================================================
.PHONY: go sync precommit test cov fmt lint lint-check lint-fix type run clean shell doctor print-activate ci

# ==============================================================================
# Main targets
# ==============================================================================

# Default: setup environment and drop into shell
go: sync shell

# ==============================================================================
# Environment-specific commands
# ==============================================================================

# Set Python/pip/precommit commands based on environment manager
ifeq ($(USE_MAMBA),1)
  define MAMBA_HOOK
  export MAMBA_ROOT_PREFIX="$(MAMBA_ROOT_PREFIX)"; eval "$$($(MAMBA) shell hook -s bash)";
  endef

  PY := MAMBA_ROOT_PREFIX="$(MAMBA_ROOT_PREFIX)" $(MAMBA) run -n $(MAMBA_ENV) python
  PIP := MAMBA_ROOT_PREFIX="$(MAMBA_ROOT_PREFIX)" $(MAMBA) run -n $(MAMBA_ENV) python -m pip
  PRECOMMIT := MAMBA_ROOT_PREFIX="$(MAMBA_ROOT_PREFIX)" $(MAMBA) run -n $(MAMBA_ENV) pre-commit
else
  PY := $(VENV)/bin/python
  PIP := $(VENV)/bin/pip
  PRECOMMIT := $(VENV)/bin/pre-commit
endif

# ==============================================================================
# Environment setup
# ==============================================================================

# Synchronize environment (create/update virtual environment and install dependencies)
# Uses micromamba on Sciris hosts, otherwise uses uv or venv
sync:
	@set -e
	@if [ "$(USE_MAMBA)" = "1" ]; then \
		echo ">> Using micromamba env '$(MAMBA_ENV)' for X11/xcb on $(HOSTNAME)"; \
		if ! command -v $(MAMBA) >/dev/null 2>&1; then \
			echo ">> micromamba not found; installing to $$HOME/bin"; \
			mkdir -p "$$HOME/bin"; \
			tmpdir="$$(mktemp -d)"; \
			curl -L https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj -C "$$tmpdir" bin/micromamba; \
			mv "$$tmpdir/bin/micromamba" "$$HOME/bin/micromamba"; \
			rm -rf "$$tmpdir"; \
		fi; \
		$(MAMBA_HOOK) \
		$(MAMBA) create -y -n "$(MAMBA_ENV)" -c conda-forge \
			python="$(PYVER)" \
			pyqt \
			numpy \
			scalene \
			websockets \
			inputimeout \
			xcb-util-wm xcb-util-renderutil \
			xorg-libx11 xorg-libxext xorg-libxrender xorg-libxcb xorg-libxau xorg-libxdmcp \
			pip setuptools wheel; \
		$(PIP) install -e . --no-deps; \
		$(PIP) install -r requirements.txt; \
	else \
		if command -v uv >/dev/null 2>&1; then \
			echo ">> Using uv to provision Python $(PYVER)"; \
			uv python install $(PYVER) || true; \
			rm -rf $(VENV); \
			uv sync --python "$$(uv python find $(PYVER))" --all-groups; \
		else \
			echo ">> uv not found, falling back to system python$(PYVER) if available"; \
			command -v python$(PYVER) >/dev/null 2>&1 || { echo "ERROR: python$(PYVER) not found."; exit 1; }; \
			rm -rf $(VENV); \
			python$(PYVER) -m venv $(VENV) || { echo "venv failed; try: python$(PYVER) -Im ensurepip --upgrade --default-pip"; exit 1; }; \
			"$(PY)" -Im ensurepip --upgrade --default-pip || true; \
			"$(PIP)" install --upgrade pip wheel; \
			"$(PIP)" install -e .; \
			"$(PIP)" install -r requirements.txt; \
		fi; \
	fi
	@$(PRECOMMIT) install

precommit:
	$(PRECOMMIT) run --all-files

# ==============================================================================
# Tests / Coverage
# ==============================================================================
test:
	QT_QPA_PLATFORM=offscreen $(PY) -m pytest -q --gui

cov:
	QT_QPA_PLATFORM=offscreen $(PY) -m pytest --gui --cov=Fish/Common --cov=Fish/Player --cov=Fish/Admin --cov-config=.coveragerc --cov-report=term-missing

# ==============================================================================
# Linting and formatting
# ==============================================================================
lint: lint-fix

lint-check:
	@echo ">>> black --check $(LINT_DIRS)"
	$(PY) -m black --check $(LINT_DIRS)
	@echo ">>> isort --check-only $(LINT_DIRS)"
	$(PY) -m isort --check-only $(LINT_DIRS)
	@echo ">>> flake8 $(LINT_DIRS)"
	$(PY) -m flake8 $(LINT_DIRS)
	@echo ">>> pydocstyle $(LINT_DIRS)"
	$(PY) -m pydocstyle $(LINT_DIRS)

lint-fix:
	@echo ">>> isort $(LINT_DIRS)"
	$(PY) -m isort $(LINT_DIRS)
	@echo ">>> black $(LINT_DIRS)"
	$(PY) -m black $(LINT_DIRS)

fmt: lint-fix

# ==============================================================================
# Type checking
# ==============================================================================
type:
	$(PY) -m mypy $(LINT_DIRS)

# ==============================================================================
# Run and clean
# ==============================================================================
MOD ?= Admin.referee
SCRIPT ?=

run:
	@export QT_XCB_GL_INTEGRATION=none; export QT_OPENGL=software; \
	if [ -n "$(SCRIPT)" ]; then \
		$(PY) "$(SCRIPT)"; \
	else \
		$(PY) -m $(MOD); \
	fi

clean:
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov dist build *.egg-info **/__pycache__ $(VENV)
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "__pycache__" -delete

# ==============================================================================
# Convenience / utility targets
# ==============================================================================

# Launch interactive shell with activated environment
shell:
	@if [ "$(USE_MAMBA)" = "1" ]; then \
		echo "Spawning interactive shell with micromamba env $(MAMBA_ENV)"; \
		bash --rcfile <(echo '$(MAMBA_HOOK) micromamba activate "$(MAMBA_ENV)"; PS1="(fishgame) [\u@\h \W]\$$ "') -i; \
	else \
		echo "Spawning interactive shell with $(VENV) activated (Python $(PYVER))"; \
		bash --rcfile <(echo 'source "$(VENV)/bin/activate"; PS1="(venv) $$PS1"') -i; \
	fi

print-activate:
	@echo "USE_MAMBA=auto (default) -> Sciris uses micromamba, others use .venv"
	@echo "USE_MAMBA=1 -> micromamba activate $(MAMBA_ENV)"
	@echo "USE_MAMBA=0 -> source $(VENV)/bin/activate"

doctor:
	@echo "Host:   $(HOSTNAME)"
	@echo "Mamba?: $(USE_MAMBA)"
	@echo "Python: $$($(PY) -V 2>/dev/null || echo MISSING)"
	@echo "PyQt5:  $$($(PY) -c 'import PyQt5; print(PyQt5.__version__)' 2>/dev/null || echo MISSING)"
	@echo "DISPLAY=$(DISPLAY)"

ci:
	@echo "=== Running CI Pipeline (all checks, no early exit) ==="
	-$(MAKE) fmt
	-$(MAKE) lint-check
	-$(MAKE) type
	-$(MAKE) test
	-$(MAKE) cov
	@echo "=== CI Pipeline Complete (check output above for any failures) ==="
