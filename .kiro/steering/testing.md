---
inclusion: fileMatch
fileMatchPattern: ["tests/**/*.py", "**/test_*.py", "conftest.py"]
---
# Testing rules

- Every correctness property P1–P17 in the design documents has at least one Hypothesis
  test that cites the property and requirement IDs in its docstring.
- Oracles for money math use `fractions.Fraction`, independently of the implementation.
- Use the `ci` Hypothesis profile (derandomized) in CI; `dev` locally.
- Container-only tests are marked `@pytest.mark.isolation` and skip unless
  `VK_ISOLATION=enforced`.
- Do not mark contract tests `xfail` or `skip` to get green builds.
- Report test counts only from actual runs.
