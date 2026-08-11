# scripts/setup_ci.py
import os


def setup_github_actions():
    wf_dir = ".github/workflows"
    os.makedirs(wf_dir, exist_ok=True)
    wf_file = os.path.join(wf_dir, "spec-validation.yml")

    yaml_content = """name: Spec Validation CI

on:
  push:
    branches: [ "main", "master" ]
  pull_request:
    branches: [ "main", "master" ]

jobs:
  lint-specs:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Run Spec Linter
        run: python scripts/ci_spec_lint.py
"""
    with open(wf_file, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    print(f"✅ Created CI workflow file at {wf_file}")


if __name__ == "__main__":
    setup_github_actions()
