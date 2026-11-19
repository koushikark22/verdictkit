# Third-domain reuse proof (core task 12, requirement core 10.3)

A "receipt total" claim type (line items → total) implemented here with **zero changes to
`core/src/verdictkit`**. It ships a golden bundle that CI replays to `REPRODUCED` or
`REPRODUCED_ACROSS_ENV`. The contract tests use an equivalent claim type in
`tests/contract/receipt_claimtype.py`.

`claim.json` is the gate input. Its `stated_total` is deliberately 1.00 higher than the
sum of the items (22.75), so the gate run must produce a CONTRADICTED finding with a
counterexample. It is a constructed example, not a real receipt.
