module.exports = {
    root: true, // This is critical - tells ESLint not to look in parent directories
    env: {
      browser: true,
      es2021: true,
      node: true,
    },
    extends: [
      'eslint:recommended',
      'plugin:react/recommended'
    ],
    parserOptions: {
      ecmaFeatures: {
        jsx: true
      },
      ecmaVersion: 'latest',
      sourceType: 'module'
    },
    plugins: [
      'react'
    ],
    settings: {
      react: {
        version: 'detect'
      }
    },
    // Customize or disable rules as needed
    rules: {
      'react/prop-types': 'off', // Example: disable prop-types rule
      'no-unused-vars': 'warn' // Example: downgrade unused vars to warnings
    }
  };