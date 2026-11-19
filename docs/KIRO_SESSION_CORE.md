# Starting the verdictkit-core Kiro session (paste into Kiro)

1. Open the repo root in Kiro. Confirm the 6 steering files are listed and the 3 hooks are enabled.
2. New Spec → Feature → name `verdictkit-core`. Paste:

> Build the VerdictKit core from the existing brief in `.kiro/specs/verdictkit-core/`
> (requirements, design, tasks), `docs/ARCHITECTURE.md`, and `docs/API_CONTRACT.md`.
> Treat the signatures in `core/src/verdictkit/**` as fixed and `tests/contract/` as the
> acceptance contract; never weaken a contract test. Run requirements analysis first and
> list any contradictions you find before writing design. Implementation order:
> tasks 1–11.4, then 12, then 13.1–13.2 and 15, so that intake → freeze → blind → execute →
> reveal → verdict → export → replay works end to end before any app logic. Generate
> property-based tests for P1–P12 from the design. Stop at checkpoint 13 and report the
> output of `scripts/gate_nov22.sh` verbatim.

3. Record every contradiction Kiro reports, every property-test bug it finds and every hook
   run that blocks a regression in `docs/KIRO_USAGE.md` (evidence log).
4. Gate: `bash scripts/gate_nov22.sh` from WSL2 (or Linux/macOS) with Docker running.
   Commit `gate/transcript.txt` and the XML files. Report the TOTAL line exactly as printed.
