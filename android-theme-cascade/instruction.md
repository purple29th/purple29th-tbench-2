# Setting

This repo is a small Android-style Kotlin project that simulates an in-house theming system (themes, inheritance, component overrides, and state-based overrides). The current implementation has bugs — running it against test scenarios produces wrong results. Your job is to fix the resolver so the project produces correct resolved tokens.

# How theme resolution is supposed to work

- **Theme inheritance:** Themes can inherit from a parent theme. Resolving tokens starts from the base of the parent chain and layers more specific values on top. A child theme's value overrides its parent's value for the same token.
- **Component overrides:** Components may define token overrides that apply whenever resolving tokens for that component, regardless of state. These overrides take precedence over tokens coming from the theme chain.
- **State overrides:** Components may define state-specific overrides (e.g. `pressed`, `focused`, `disabled`). Only the override for the requested state applies, and it wins over both component overrides and theme tokens.

# Active theme vs explicit apply()

The app has a current active theme that components use by default. A component can also be explicitly bound to a specific theme via an `apply(theme)` binding. Explicitly applied components keep that theme even if the active theme later changes.

# Deliverable

Running the app against a provided scenario must write `/app/output.json`, containing resolved token maps for each `(component, state)` query in the scenario, in the same order as the input queries.

# How to run

The source lives under `/app/src/`. Build and run with:

  bash /app/src/run.sh

This script compiles the Kotlin sources via `kotlinc` and runs the app, which reads `/app/scenario.json` and writes `/app/output.json`.

# Where to start

The resolver implementation is in `/app/src/com/example/theme/ThemeResolver.kt`. Read the bug behavior by running the app against test scenarios and comparing output to expected behavior.
