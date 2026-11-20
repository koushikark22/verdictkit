#!/usr/bin/env python3
"""VerdictKit Reel acquisition staging: not an evidence-admission decision.

Dependencies: Python standard library only. Does not modify forensic engine.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import urllib.parse
import urllib.request

UTC = dt.timezone.utc
GRANULARITIES = {60, 300, 900, 3600, 21600, 86400}
MAX_BARS = 300
MAX_BYTES = 2 * 1024 * 1024
HOST = 'api.exchange.coinbase.com'

class EvidenceBlocked(ValueError):
    pass

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def parse_utc(value):
    if not value.endswith('Z'):
        raise EvidenceBlocked('Time must end in Z (UTC)')
    try:
        x = dt.datetime.fromisoformat(value[:-1] + '+00:00')
    except ValueError as exc:
        raise EvidenceBlocked('Invalid ISO-8601 UTC timestamp') from exc
    if x.microsecond:
        raise EvidenceBlocked('Fractional seconds not supported')
    return x

def stamp(x):
    return x.astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')

def check_request(product, start, end, granularity):
    if granularity not in GRANULARITIES:
        raise EvidenceBlocked('Unsupported granularity')
    if not product or len(product) > 40 or not all(c.isascii() and (c.isupper() or c.isdigit() or c == '-') for c in product):
        raise EvidenceBlocked('Invalid product ID')
    a, b = parse_utc(start), parse_utc(end)
    seconds = int((b-a).total_seconds())
    if seconds <= 0 or seconds % granularity or seconds // granularity > MAX_BARS:
        raise EvidenceBlocked('Time window invalid or exceeds 300 bars')
    if int(a.timestamp()) % granularity or int(b.timestamp()) % granularity:
        raise EvidenceBlocked('Window must align to candle boundaries')
    if b > dt.datetime.now(UTC) - dt.timedelta(seconds=granularity):
        raise EvidenceBlocked('Incomplete/recent candles are not accepted')
    return a, b, seconds // granularity

def normalize(payload, start, end, granularity):
    if not isinstance(payload, list):
        raise EvidenceBlocked('Unexpected provider response')
    a, b, expected = check_request('BTC-USD', start, end, granularity)
    out = {}
    for row in payload:
        if not isinstance(row, list) or len(row) != 6:
            raise EvidenceBlocked('Unexpected candle row shape')
        t, low, high, opn, close, volume = row
        # Require JSON numeric types only, rejecting booleans and provider string coercion.
        if type(t) is not int or any(type(v) not in (int, float) for v in (low, high, opn, close, volume)):
            raise EvidenceBlocked('Invalid numeric candle fields')
        if any(not (float('-inf') < float(v) < float('inf')) for v in (low, high, opn, close, volume)):
            raise EvidenceBlocked('Non-finite candle fields')
        # Coinbase may include the exact exclusive end boundary. It is not
        # part of the requested [start, end) interval and is never persisted.
        if t == int(b.timestamp()):
            continue
        if t < int(a.timestamp()) or t >= int(b.timestamp()) or t % granularity:
            raise EvidenceBlocked('Out-of-window or misaligned candle')
        if t in out:
            raise EvidenceBlocked('Duplicate candle')
        if not (0 < low <= min(opn, close) <= max(opn, close) <= high) or volume < 0:
            raise EvidenceBlocked('OHLCV invariant violation')
        # repr gives round-trippable rendering, but exact source bytes are separately hashed.
        out[t] = {'time': stamp(dt.datetime.fromtimestamp(t, UTC)),
                  'open': repr(opn), 'high': repr(high), 'low': repr(low),
                  'close': repr(close), 'volume': repr(volume)}
    expected_times = range(int(a.timestamp()), int(b.timestamp()), granularity)
    if len(out) != expected or any(t not in out for t in expected_times):
        raise EvidenceBlocked('Missing candles: provider may omit no-trade intervals')
    return [out[t] for t in expected_times]

def fetch(product, start, end, granularity, opener=None):
    check_request(product, start, end, granularity)
    params = urllib.parse.urlencode({'start': start, 'end': end, 'granularity': str(granularity)})
    url = 'https://' + HOST + '/products/' + product + '/candles?' + params
    req = urllib.request.Request(url, headers={'User-Agent': 'VerdictKit-Evidence-Staging/1.0', 'Accept': 'application/json'}, method='GET')
    if opener is None:
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                raise EvidenceBlocked('Provider redirect rejected')
        client = urllib.request.build_opener(NoRedirect)
        opener = client.open
    with opener(req, timeout=20) as response:
        if response.status != 200:
            raise EvidenceBlocked('Provider returned non-200 status')
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise EvidenceBlocked('Provider response exceeds size limit')
        content_type = response.headers.get('Content-Type', '')
        if 'json' not in content_type.lower():
            raise EvidenceBlocked('Unexpected response content type')
    try:
        raw = json.loads(data)
    except (ValueError, UnicodeDecodeError) as exc:
        raise EvidenceBlocked('Provider returned invalid JSON') from exc
    bars = normalize(raw, start, end, granularity)
    return url, data, bars

def build_record(product, start, end, granularity, url, raw, bars, retrieved_at=None):
    check_request(product, start, end, granularity)
    if not url.startswith('https://' + HOST + '/products/' + product + '/candles?'):
        raise EvidenceBlocked('Source URL not authorized')
    if not isinstance(raw, bytes):
        raise EvidenceBlocked('Raw response must be bytes')
    if normalize(json.loads(raw), start, end, granularity) != bars:
        raise EvidenceBlocked('Bars differ from provider response')
    if retrieved_at is None:
        retrieved_at = stamp(dt.datetime.now(UTC))
    return {'schema': 'verdictkit.reel.ohlcv.staging.v1',
            'admission': 'BLOCKED', 'admissionReason': 'EVIDENCE_RIGHTS_UNVERIFIED',
            'dataMode': 'LIVE_EVIDENCE', 'demonstrationOnly': False,
            'providerId': 'coinbase-exchange', 'origin': 'EXCHANGE',
            'independenceBasis': 'INDEPENDENT_OF_CLAIMANT',
            'rightsBasis': 'UNVERIFIED', 'licenseClass': 'REFETCH_ONLY',
            'embeddedInBundle': False, 'authenticity': 'NOT_ESTABLISHED',
            'uri': url, 'retrievedAt': retrieved_at,
            'productId': product, 'start': start, 'end': end,
            'granularitySeconds': granularity, 'barCount': len(bars),
            'providerResponseSha256': hashlib.sha256(raw).hexdigest(),
            'snapshotHash': digest(bars), 'bars': bars}

def verify_record(record):
    if not isinstance(record, dict) or record.get('schema') != 'verdictkit.reel.ohlcv.staging.v1':
        raise EvidenceBlocked('Unknown staging schema')
    if (record.get('admission'), record.get('rightsBasis'), record.get('licenseClass'),
        record.get('embeddedInBundle'), record.get('authenticity')) != (
        'BLOCKED', 'UNVERIFIED', 'REFETCH_ONLY', False, 'NOT_ESTABLISHED'):
        raise EvidenceBlocked('Unsafe provenance or admission state')
    product, start, end, step = (record.get(k) for k in ('productId','start','end','granularitySeconds'))
    if record.get('providerId') != 'coinbase-exchange' or record.get('origin') != 'EXCHANGE' or record.get('independenceBasis') != 'INDEPENDENT_OF_CLAIMANT':
        raise EvidenceBlocked('Provider provenance metadata mismatch')
    if not isinstance(record.get('uri'), str) or not record['uri'].startswith('https://' + HOST + '/products/' + product + '/candles?'):
        raise EvidenceBlocked('Provider URI mismatch')
    if record.get('dataMode') != 'LIVE_EVIDENCE' or record.get('demonstrationOnly') is not False:
        raise EvidenceBlocked('Data mode mismatch')
    if not isinstance(record.get('providerResponseSha256'), str) or len(record['providerResponseSha256']) != 64:
        raise EvidenceBlocked('Provider response digest missing')
    _, _, count = check_request(product, start, end, step)
    bars = record.get('bars')
    if not isinstance(bars, list) or len(bars) != count or record.get('barCount') != count:
        raise EvidenceBlocked('Bar count mismatch')
    if digest(bars) != record.get('snapshotHash'):
        raise EvidenceBlocked('Snapshot tampering detected')
    times = [stamp(parse_utc(x['time'])) for x in bars]
    a = int(parse_utc(start).timestamp())
    expected = [stamp(dt.datetime.fromtimestamp(a+i*step,UTC)) for i in range(count)]
    if times != expected:
        raise EvidenceBlocked('Non-deterministic candle timeline')
    for row in bars:
        try:
            from decimal import Decimal
            lo, hi, op, cl, vol = (Decimal(row[k]) for k in ('low','high','open','close','volume'))
        except Exception as exc:
            raise EvidenceBlocked('Invalid decimal bar values') from exc
        if not all(x.is_finite() for x in (lo, hi, op, cl, vol)) or not (0 < lo <= min(op,cl) <= max(op,cl) <= hi) or vol < 0:
            raise EvidenceBlocked('OHLCV invariant violation')
    return {'integrity': 'VERIFIED', 'admission': 'BLOCKED',
            'admissionReason': 'EVIDENCE_RIGHTS_UNVERIFIED', 'snapshotHash': record['snapshotHash'],
            'barCount': count, 'authenticity': 'NOT_ESTABLISHED'}

def atomic_write(path, record):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise EvidenceBlocked('Output already exists; refusing overwrite')
    fd, temp = tempfile.mkstemp(prefix='.vk-reel-', suffix='.tmp', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(canonical(record) + b'\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)

def main(argv=None):
    p = argparse.ArgumentParser(description='Acquire or verify BLOCKED staging OHLCV; never auto-admits live evidence')
    sub = p.add_subparsers(dest='operation', required=True)
    ac = sub.add_parser('acquire')
    ac.add_argument('--product', required=True)
    ac.add_argument('--start', required=True)
    ac.add_argument('--end', required=True)
    ac.add_argument('--granularity', type=int, required=True)
    ac.add_argument('--output', required=True)
    vf = sub.add_parser('verify')
    vf.add_argument('--input', required=True)
    args = p.parse_args(argv)
    try:
        if args.operation == 'acquire':
            url, raw, bars = fetch(args.product, args.start, args.end, args.granularity)
            record = build_record(args.product, args.start, args.end, args.granularity, url, raw, bars)
            atomic_write(args.output, record)
            print(json.dumps({'stagingPath': args.output, **verify_record(record)}, indent=2))
        else:
            record = json.loads(Path(args.input).read_text(encoding='utf-8'))
            print(json.dumps(verify_record(record), indent=2))
        return 0
    except (EvidenceBlocked, OSError, ValueError, KeyError, TypeError) as exc:
        print('BLOCKED: ' + str(exc), file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
