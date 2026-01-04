import js from '@eslint/js';
import globals from 'globals';

export default [
  js.configs.recommended,
  {
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: {
        ...globals.browser,
        marked: 'readonly',
      },
    },
    rules: {
      // Best practices
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      'no-console': 'off',
      'prefer-const': 'warn',
      'no-var': 'error',

      // Style (Prettier handles most, but these complement it)
      eqeqeq: ['error', 'always'],
      curly: ['error', 'multi-line'],
      'no-multi-spaces': 'error',

      // Error prevention
      'no-undef': 'error',
      'no-unreachable': 'error',
      'no-duplicate-case': 'error',
    },
  },
  {
    ignores: ['node_modules/', 'dist/', 'build/', '*.min.js'],
  },
];
