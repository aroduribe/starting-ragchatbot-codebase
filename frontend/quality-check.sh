#!/bin/bash

# Frontend Quality Check Script
# Run this script to check code quality for the frontend

set -e

echo "========================================"
echo "Frontend Code Quality Check"
echo "========================================"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

echo ""
echo "1. Checking code formatting with Prettier..."
echo "----------------------------------------"
npm run format:check || {
    echo ""
    echo "Formatting issues found. Run 'npm run format' to fix."
    FORMATTING_FAILED=1
}

echo ""
echo "2. Linting JavaScript with ESLint..."
echo "----------------------------------------"
npm run lint:js || {
    echo ""
    echo "ESLint issues found. Run 'npm run lint:js:fix' to auto-fix."
    ESLINT_FAILED=1
}

echo ""
echo "3. Linting CSS with Stylelint..."
echo "----------------------------------------"
npm run lint:css || {
    echo ""
    echo "Stylelint issues found. Run 'npm run lint:css:fix' to auto-fix."
    STYLELINT_FAILED=1
}

echo ""
echo "========================================"
if [ -n "$FORMATTING_FAILED" ] || [ -n "$ESLINT_FAILED" ] || [ -n "$STYLELINT_FAILED" ]; then
    echo "Some checks failed. Run 'npm run quality:fix' to auto-fix issues."
    exit 1
else
    echo "All quality checks passed!"
fi
echo "========================================"
