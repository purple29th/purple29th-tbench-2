# Setting

This repo is a small Android-style Kotlin project that simulates an in-house theming system (themes, inheritance, component overrides, and state-based overrides). The current implementation has bugs — running it against test scenarios produces wrong results. Your job is to fix the resolver so the project produces correct resolved tokens.

# How theme resolution is supposed to work

- **Theme inheritance:** Themes can inherit from a parent theme. A child theme's value overrides its parent's value for the same token.
- **Component overrides:** Components may define token overrides that apply whenever resolving tokens for that component.
- **State overrides:** Components may define state-specific overrides (e.g. `pressed`, `focused`, `disabled`).

# Contract tests

A set of contract tests in `/app/src/com/example/theme/test/ResolverContract.kt` documents the expected resolver behavior. Run them with:

  bash /app/src/run-contract.sh

The contract tests are your specification — make all of them pass. Each test names a behavior the resolver must satisfy.

# Deliverable

Once the contract tests pass, running the app against a scenario must write `/app/output.json` with resolved token maps for each `(component, state)` query, in input order:

  bash /app/src/run.sh

# Where to start

The resolver implementation is in `/app/src/com/example/theme/ThemeResolver.kt`. Run the contract tests, see which fail, and fix the resolver until they all pass.
