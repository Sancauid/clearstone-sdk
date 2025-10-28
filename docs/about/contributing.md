# Contributing to the Clearstone SDK

We're thrilled you're interested in contributing to the Clearstone SDK! Your contributions help us build a more robust and reliable toolkit for the entire AI agent ecosystem. This document provides guidelines to ensure a smooth and effective contribution process.

## How Can I Contribute?

There are many ways to contribute, and all are valuable. Here are a few ideas:

*   🐛 **Reporting Bugs:** If you find a bug, please [open an issue](https://github.com/your-repo/clearstone-sdk/issues) and provide as much detail as possible, including steps to reproduce it.
*   ✨ **Suggesting Enhancements:** Have an idea for a new feature, a pre-built policy, or an improvement to an existing one? We'd love to hear it. [Open an issue](https://github.com/your-repo/clearstone-sdk/issues) with the "enhancement" label.
*   📝 **Improving Documentation:** If you find parts of the documentation that are unclear, confusing, or incomplete, a pull request with improvements is highly appreciated.
*   💻 **Contributing Code:** If you're ready to write some code, you can pick up an existing issue or propose a new feature of your own.

## Development Setup

To get started with the codebase, you'll need to set up a local development environment.

#### Prerequisites
*   Git
*   Python 3.10+
*   A fork of the repository.

#### Step-by-Step Guide

1.  **Fork & Clone the Repository**

    First, fork the repository to your own GitHub account. Then, clone your fork locally:
    ```bash
    git clone https://github.com/YOUR_USERNAME/clearstone-sdk.git
    cd clearstone-sdk
    ```

2.  **Create a Virtual Environment**

    It is highly recommended to work inside a Python virtual environment to isolate project dependencies.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Dependencies**

    Install the package in "editable" mode along with all development dependencies (like `pytest`, `black`, and `ruff`). This allows you to edit the code and have the changes immediately reflected.
    ```bash
    pip install -e ".[dev]"
    ```

4.  **Run the Test Suite**

    Before making any changes, ensure that the existing test suite passes. This is a crucial first step.
    ```bash
    pytest
    ```

## Pull Request Process

We follow a standard, automated pull request workflow.

1.  **Create a Feature Branch**

    Create a new branch from `main` for your changes. Please use a descriptive name.
    ```bash
    git checkout -b feature/my-new-policy-validator
    ```

2.  **Make Your Changes**

    Write your code! Follow the existing code style and structure. Remember to add docstrings and type hints.

3.  **Add or Update Tests**

    Any new feature or bug fix **must** be accompanied by tests.
    *   Bug fixes should include a test that fails without the fix and passes with it.
    *   New features must have corresponding unit or integration tests.

4.  **Format and Lint Your Code (CRITICAL STEP)**

    Before committing, you must run our automated formatting and linting tools. Our CI pipeline will fail your pull request if this step is skipped.
    ```bash
    # Automatically format all code to the project's style
    black .

    # Automatically fix any fixable linting errors
    ruff check . --fix

    # Check for any remaining, non-fixable errors
    ruff check .
    ```

5.  **Ensure All Local Checks Pass**

    Run the full test suite one last time to ensure you haven't introduced any regressions.
    ```bash
    pytest
    ```

6.  **Submit the Pull Request**

    Push your branch to your fork and open a pull request against the `main` branch of the original repository.
    *   Our GitHub Actions CI will automatically run all tests and style checks. All checks must pass before the PR can be merged.
    *   Use a clear and descriptive title (e.g., "feat: Add PolicyMetrics collector for observability").
    *   Provide a detailed description of the changes.
    *   If your PR addresses an existing issue, link it using `Fixes #123`.

## Coding Style Guide

*   Our code style is enforced automatically by **Black** (for formatting) and **Ruff** (for linting).
*   Please run `black .` and `ruff check . --fix` before committing your changes.
*   Docstrings should follow the **Google Python Style Guide**.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## License Agreement

By contributing to the Clearstone SDK, you agree that your contributions will be licensed under its MIT License.