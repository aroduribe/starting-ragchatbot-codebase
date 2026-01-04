# Frontend Code Quality Tools

This document describes the code quality tools added to the frontend development workflow.

## Overview

Essential code quality tools have been added to ensure consistent formatting and catch common issues in JavaScript, CSS, and HTML files.

## Tools Added

### 1. Prettier (Code Formatter)
- **Purpose**: Automatic code formatting for JS, CSS, HTML, and JSON files
- **Config file**: `frontend/.prettierrc`
- **Settings**:
  - Single quotes for strings
  - Semicolons required
  - 2-space indentation
  - 100 character line width
  - Trailing commas in ES5 locations

### 2. ESLint (JavaScript Linter)
- **Purpose**: Catch JavaScript errors and enforce best practices
- **Config file**: `frontend/eslint.config.js`
- **Key rules**:
  - `no-var`: Prefer `const`/`let` over `var`
  - `eqeqeq`: Require strict equality (`===`)
  - `prefer-const`: Suggest `const` when variable is never reassigned
  - `no-undef`: Catch undefined variables
  - Console logging allowed (useful for debugging)

### 3. Stylelint (CSS Linter)
- **Purpose**: Catch CSS errors and enforce consistent styling
- **Config file**: `frontend/.stylelintrc.json`
- **Extends**: `stylelint-config-standard`
- **Customizations**: Relaxed rules for ID selectors, vendor prefixes, and keyframe naming to work with existing codebase

## NPM Scripts

Run these commands from the `frontend/` directory:

| Command | Description |
|---------|-------------|
| `npm run format` | Format all files with Prettier |
| `npm run format:check` | Check if files are formatted (CI-friendly) |
| `npm run lint:js` | Lint JavaScript with ESLint |
| `npm run lint:js:fix` | Auto-fix ESLint issues |
| `npm run lint:css` | Lint CSS with Stylelint |
| `npm run lint:css:fix` | Auto-fix Stylelint issues |
| `npm run lint` | Run all linters |
| `npm run lint:fix` | Auto-fix all lint issues |
| `npm run quality` | Check formatting + run all linters |
| `npm run quality:fix` | Fix formatting + fix all lint issues |

## Quick Start

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install

# Check code quality
npm run quality

# Auto-fix all issues
npm run quality:fix
```

## Shell Script

A convenience script `frontend/quality-check.sh` is provided for running all quality checks with descriptive output:

```bash
cd frontend
./quality-check.sh
```

## Files Created

| File | Purpose |
|------|---------|
| `frontend/package.json` | NPM dependencies and scripts |
| `frontend/.prettierrc` | Prettier configuration |
| `frontend/.prettierignore` | Files to ignore for formatting |
| `frontend/eslint.config.js` | ESLint configuration (flat config) |
| `frontend/.stylelintrc.json` | Stylelint configuration |
| `frontend/quality-check.sh` | Shell script for quality checks |

## Files Modified

| File | Changes |
|------|---------|
| `frontend/script.js` | Formatted with Prettier; renamed unused `e` to `_e` |
| `frontend/style.css` | Formatted with Prettier |
| `frontend/index.html` | Formatted with Prettier |
| `.gitignore` | Added `node_modules/` and `package-lock.json` |

## Integration Notes

- The quality tools are isolated to the `frontend/` directory
- No changes to Python/backend tooling
- ESLint uses the modern flat config format (ESLint 9.x)
- All tools are installed as devDependencies (not needed in production)
