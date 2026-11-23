"""Fetch the Texas statute pages, hash the raw response bodies, and print the canonical
TX.json and MANIFEST.json contents (decision B7). Pass --write to update the files.

Warning: statutes.capitol.texas.gov serves a JavaScript app shell for these URLs, so the
hash covers that shell and not the statute text. Review the printed body sizes.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

URIS = [f"https://statutes.capitol.texas.gov/Docs/TX/htm/TX.{n}.htm" for n in (151, 152, 321)]
OUT = Path(__file__).resolve().parents[1] / "apps/quote-autopsy/src/quote_autopsy/rules"


def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "core/src"))
    from verdictkit.canonical import canonical_bytes

    today = datetime.date.today().isoformat()
    sources = []
    for uri in URIS:
        req = urllib.request.Request(uri, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read()
        print(f"{uri} {len(body)} bytes", file=sys.stderr)
        sources.append({"retrieved_at": today, "sha256_of_source": hashlib.sha256(body).hexdigest(),
                        "uri": uri})
    doc = {"doc_fee_cap": None, "local_rate_max_pct": "2.00", "local_rate_min_pct": "0.00",
           "localities": None, "sources": sources, "state": "TX", "state_rate_pct": "6.25"}
    data = canonical_bytes(doc)
    manifest = json.dumps({"files": {"TX.json": hashlib.sha256(data).hexdigest()}},
                          sort_keys=True, separators=(",", ":"))
    print(data.decode()), print(manifest)
    if "--write" in sys.argv:
        (OUT / "TX.json").write_bytes(data)
        (OUT / "MANIFEST.json").write_text(manifest, encoding="utf-8")


if __name__ == "__main__":
    main()
