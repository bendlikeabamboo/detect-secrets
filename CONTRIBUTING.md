# Contributing

Thanks for your interest in helping to grow this repository, and make it better
for developers everywhere! This document serves as a guide to help you quickly
gain familarity with the repository, and start your development environment so
that you can quickly hit the ground running.

## 1. Learn the Overall Layout of the Code

Be sure to read through the [overview of `detect-secrets`' design](/docs/design.md) before
starting to work on it! This will give you a better idea of the different components to the
system, and how they interact together to find secrets.

## 2. Building Your Development Environment

This project uses [uv](https://docs.astral.sh/uv/) to manage dependencies and
virtual environments. To set up your development environment (including the
git pre-commit hooks), run:

```bash
make setup
```

This is equivalent to:

```bash
uv sync
uv run pre-commit install --install-hooks
```

You can check to see whether you're successful by executing:

```bash
uv run detect-secrets --version
```

## 3. Run tests

Tests should succeed on master. Any code additions you contribute will also need testing
so it's good to run tests first to make sure you have a working copy. Don't worry -- the tests
don't take long!

```bash
$ time uv run pytest tests
...
real    0m10.113s
user    0m6.848s
sys     0m2.486s
```

### Running the Entire Test Suite

You can run the full quality gate (test suite with coverage floors, type checking
with `ty`, and all pre-commit hooks) by doing:

```bash
make test
```

This runs the equivalent of:

```bash
uv run coverage run -m pytest --strict-markers tests
uv run coverage report --include=tests/* --fail-under 99
uv run coverage report --include=testing/* --fail-under 100
uv run coverage report --include=detect_secrets/* --fail-under 95
uv run ty check
uv run pre-commit run --all-files
```

To test against a specific Python version, use:

```bash
uv sync --python 3.13
```

### Running a Specific Test

With `pytest`, you can specify tests you want to run in multiple granularity
levels. Here are a couple of examples:

- Running all tests related to `core/baseline.py`

  ```bash
  uv run pytest tests/core/baseline_test.py
  ```

- Running a single test class

  ```bash
  uv run pytest tests/core/baseline_test.py::TestCreate
  ```

- Running a single test function, inside test class

  ```bash
  uv run pytest tests/core/baseline_test.py::TestCreate::test_basic_usage
  ```

- Running a single root level test function

  ```bash
  uv run pytest tests/plugins/baseline_test.py::test_upgrade_succeeds
  ```

Generally speaking, we use test classes to group a series of related test cases together (e.g.
`TestCreate` tests the `detect_secrets.core.baseline.create` functionality), but root test
functions otherwise. If you're writing tests for your plugins, you should probably just use
root test functions.

## 4. Make Your Change

Want to contribute a new plugin? Check out more details here:
[Writing Your Own Plugin](/docs/plugins.md#Writing%20Your%20Own%20Plugin)

What about contributing better false positive filters? Check out more details here:
[Writing Your Own Filter](/docs/filters.md#Writing%20Your%20Own%20Filter)

## 5. Deploying Changes

Check out [more detailed upgrade instructions here](/docs/upgrades.md), and how to write
backwards-compatible changes using the built-in upgrade infrastructure.
