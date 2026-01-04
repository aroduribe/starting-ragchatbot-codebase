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

---

# Frontend Changes: Dark/Light Theme Toggle

## Overview

Added a theme toggle button that allows users to switch between dark and light themes with smooth transitions and persistent preference storage.

## Files Modified

### 1. `frontend/index.html`

Added a theme toggle button at the top of the body, positioned in the top-right corner:

```html
<button class="theme-toggle" id="themeToggle" aria-label="Toggle theme" title="Toggle light/dark theme">
    <svg class="sun-icon">...</svg>
    <svg class="moon-icon">...</svg>
</button>
```

- Uses SVG icons for sun (light theme indicator) and moon (dark theme indicator)
- Includes proper ARIA attributes for accessibility
- Keyboard navigable with Tab key

### 2. `frontend/style.css`

#### New CSS Variables for Theming

Added new CSS variables to support both themes:
- `--code-bg` - Background color for code blocks
- `--source-link-bg`, `--source-link-border`, `--source-link-color` - Source link styling
- `--source-link-hover-bg`, `--source-link-hover-border`, `--source-link-hover-color` - Source link hover states

#### Light Theme Variables (`[data-theme="light"]`)

Created a complete light theme with:
- Light background (`#f8fafc`)
- White surface color (`#ffffff`)
- Dark text for contrast (`#1e293b`, `#64748b`)
- Softer borders (`#e2e8f0`)
- Adjusted shadows and focus rings

#### Theme Toggle Button Styles

- Fixed position in top-right corner
- Circular button (44x44px) with hover effects
- Icon visibility toggles based on current theme
- Smooth rotation animation on hover

#### Transition Effects

Added CSS transitions to key elements for smooth theme switching:
```css
transition: background-color 0.3s ease,
            border-color 0.3s ease,
            color 0.3s ease,
            box-shadow 0.3s ease;
```

### 3. `frontend/script.js`

Added three new functions:

#### `initializeTheme()`
- Called on page load
- Reads saved theme from localStorage (defaults to dark)
- Applies the saved theme

#### `toggleTheme()`
- Toggles between dark and light themes
- Called when the toggle button is clicked

#### `setTheme(theme)`
- Sets the `data-theme` attribute on the document root
- Saves preference to localStorage
- Updates button's aria-label for accessibility

## Usage

1. Click the sun/moon icon button in the top-right corner
2. Theme preference is automatically saved to localStorage
3. Preference persists across browser sessions

## Accessibility Features

- Button has `aria-label` that updates based on current theme
- Button is focusable and keyboard accessible
- Focus ring visible when button is focused
- Good color contrast maintained in both themes

## Browser Support

Uses standard CSS custom properties and localStorage, compatible with all modern browsers.
