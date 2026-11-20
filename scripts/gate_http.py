#!/usr/bin/env python3
"""Container gate: the HTTP lifecycle in judge mode through the authenticated examiner.

Run by ``entrypoint.sh gate-http`` as vk-custodian, with the examiner worker running as
vk-examiner. Fails (exit 1) unless the API starts in judge mode with ENFORCED isolation,
a quote case runs to a sealed verdict through the socket examiner, the bundle is
stamped ENFORCED, and server-side replay reproduces the verdict hash.
"""
from __future__ import annotations

import json
import sys

from fastapi.testclient import TestClient

from verdictkit.api.server import create_app

PARAMS = {
    "selling_price": "30000.00", "addons": [], "doc_fee": "500.00", "doc_fee_taxable": True,
    "gov_fees": [], "rebates": [], "trade_allowance": "0.00", "trade_payoff": "0.00",
    "trade_tax_credit": True, "cash_down": "5000.00", "stated_tax_rate_pct": "6.00",
    "apr_pct": "6.00", "term_months": 60, "jurisdiction": {"state": "TX"},
}


def expect(cond: bool, what: str) -> None:
    print(("PASS " if cond else "FAIL ") + what, flush=True)
    if not cond:
        raise SystemExit(1)


def main() -> int:
    with TestClient(create_app()) as c:
        health = c.get("/api/v1/health").json()
        expect(health["judgeMode"] is True and health["isolationMode"] == "ENFORCED",
               f"judge-mode health {json.dumps(health, sort_keys=True)}")
        created = c.post("/api/v1/cases", json={
            "claimType": "quote.finance.v1", "dataMode": "LIVE_EVIDENCE",
            "form": {"params": PARAMS, "outcomes": {"amount_financed": "27999.99"}}})
        expect(created.status_code == 201 and "27999.99" not in created.text,
               "intake accepted without echoing the asserted outcome")
        case_id = created.json()["caseId"]
        expect(c.post(f"/api/v1/cases/{case_id}/freeze").status_code == 200, "freeze")
        expect(c.post(f"/api/v1/cases/{case_id}/evidence").status_code == 200, "evidence stage")
        run = c.post(f"/api/v1/cases/{case_id}/runs")
        expect(run.status_code == 202 and run.json()["state"] == "COMPLETED",
               f"run through socket examiner: {run.status_code} {run.json().get('state')}")
        record = c.get(f"/api/v1/cases/{case_id}/runs/{run.json()['runId']}").json()
        expect(record["isolationMode"] == "ENFORCED", "run record stamped ENFORCED")
        outcome = c.get(f"/api/v1/cases/{case_id}/outcome").json()
        expect(outcome["isolationMode"] == "ENFORCED" and outcome["headline"]["status"] == "CONTRADICTED",
               f"outcome {outcome['headline']}")
        bundle = c.get(f"/api/v1/cases/{case_id}/bundle")
        meta = c.get(f"/api/v1/cases/{case_id}/bundle/metadata").json()
        expect(meta["isolationMode"] == "ENFORCED" and meta["integrity"]["status"] == "VERIFIED",
               "bundle metadata ENFORCED + integrity VERIFIED")
        replay = c.post("/api/v1/replays", content=bundle.content,
                        headers={"content-type": "application/zip"}).json()
        expect(replay["reproducibility"]["status"] == "REPRODUCED"
               and replay["reproducibility"]["replayedVerdictHash"] == outcome["verdictHash"],
               f"server replay {replay['reproducibility']['status']}")
        # SYNTHETIC_DEMO fixture: evidence is written by the custodian to VK_EVIDENCE_DIR
        # and read, hash-checked, by the examiner running as a different OS user.
        demo = c.post("/api/v1/cases", json={"claimType": "reel.mechanical.v1",
                                             "dataMode": "SYNTHETIC_DEMO",
                                             "fixtureId": "fx_reel_impossible_sma"})
        expect(demo.status_code == 201, "synthetic fixture intake")
        demo_id = demo.json()["caseId"]
        expect(c.post(f"/api/v1/cases/{demo_id}/freeze").status_code == 200, "fixture freeze")
        ev = c.post(f"/api/v1/cases/{demo_id}/evidence")
        expect(ev.status_code == 200 and ev.json()["evidence"][0]["origin"] == "SYNTHETIC_FIXTURE",
               "synthetic evidence acquired by the custodian")
        drun = c.post(f"/api/v1/cases/{demo_id}/runs")
        expect(drun.status_code == 202 and drun.json()["state"] == "COMPLETED",
               f"fixture run through socket examiner: {drun.status_code}")
        dout = c.get(f"/api/v1/cases/{demo_id}/outcome").json()
        expect(dout["isolationMode"] == "ENFORCED" and dout["demonstrationOnly"] is True
               and dout["headline"] == {"status": "IMPOSSIBLE", "confidenceClass": None},
               f"demo outcome {dout['headline']}")
        dbundle = c.get(f"/api/v1/cases/{demo_id}/bundle").content
        dreplay = c.post("/api/v1/replays", content=dbundle).json()
        expect(dreplay["reproducibility"]["status"] == "REPRODUCED",
               f"demo server replay {dreplay['reproducibility']['status']}")
        live = c.post("/api/v1/cases", json={
            "claimType": "reel.mechanical.v1", "dataMode": "LIVE_EVIDENCE",
            "form": {"params": {"instrument": "SYNTH-USD", "timeframe": "1d",
                                "start": "2025-01-01", "end": "2026-01-01",
                                "template": "BUY_AND_HOLD", "template_params": {},
                                "instrument_mode": "SPOT_LONG_FLAT"},
                     "outcomes": {"trade_count": "1"}}})
        live_id = live.json()["caseId"]
        c.post(f"/api/v1/cases/{live_id}/freeze")
        lev = c.post(f"/api/v1/cases/{live_id}/evidence")
        expect(lev.status_code == 422 and lev.json()["blockers"][0]["code"] == "POLICY_VIOLATION",
               "live case cannot use synthetic evidence")
    print("GATE-HTTP PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
