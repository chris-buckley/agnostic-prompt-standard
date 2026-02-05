#!/bin/bash
set -e

echo "==> Installing Node.js dependencies..."
npm install --prefix packages/aps-cli-node

echo "==> Installing UV (Python package manager)..."
pip install uv

echo "==> Installing Python CLI with dev dependencies..."
uv pip install --system -e "packages/aps-cli-py[dev]"

echo "==> Installing Ruff (Python linter/formatter)..."
pip install ruff

echo "==> Setting up Husky git hooks..."
npm exec --prefix packages/aps-cli-node -- husky install

echo "==> Development environment ready!"
