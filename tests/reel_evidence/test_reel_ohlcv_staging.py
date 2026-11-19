import importlib.util
import json
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[2] / 'scripts' / 'reel_ohlcv_acquire.py'
spec = importlib.util.spec_from_file_location('vk_reel_ohlcv_staging', SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

START = '2025-01-01T00:00:00Z'
END = '2025-01-01T00:02:00Z'
T = 1735689600
ROWS = [[T, 9, 12, 10, 11, 2], [T+60, 10, 13, 11, 12, 3]]
URL = 'https://api.exchange.coinbase.com/products/BTC-USD/candles?start=X'

class TestStaging(unittest.TestCase):
    def test_valid_record_stays_blocked(self):
        bars = m.normalize(ROWS, START, END, 60)
        record = m.build_record('BTC-USD', START, END, 60, URL, json.dumps(ROWS).encode(), bars)
        self.assertEqual(m.verify_record(record)['admission'], 'BLOCKED')
        self.assertEqual(record['rightsBasis'], 'UNVERIFIED')
        self.assertFalse(record['embeddedInBundle'])
    def test_exclusive_end_boundary_is_discarded(self):
        extra = [T + 120, 11, 14, 12, 13, 4]
        self.assertEqual(m.normalize(ROWS + [extra], START, END, 60),
                         m.normalize(ROWS, START, END, 60))
    def test_true_outside_window_is_rejected(self):
        extra = [T + 180, 11, 14, 12, 13, 4]
        with self.assertRaises(m.EvidenceBlocked):
            m.normalize(ROWS + [extra], START, END, 60)
    def test_gaps_rejected(self):
        with self.assertRaises(m.EvidenceBlocked):
            m.normalize(ROWS[:1], START, END, 60)
    def test_duplicates_rejected(self):
        with self.assertRaises(m.EvidenceBlocked):
            m.normalize(ROWS + ROWS[:1], START, END, 60)
    def test_bad_ohlc_rejected(self):
        bad = [list(r) for r in ROWS]
        bad[0][1] = 11.5
        with self.assertRaises(m.EvidenceBlocked):
            m.normalize(bad, START, END, 60)
    def test_tampering_rejected(self):
        bars = m.normalize(ROWS, START, END, 60)
        record = m.build_record('BTC-USD', START, END, 60, URL, json.dumps(ROWS).encode(), bars)
        record['bars'][0]['close'] = '11.5'
        with self.assertRaises(m.EvidenceBlocked):
            m.verify_record(record)
    def test_rights_promotion_rejected(self):
        bars = m.normalize(ROWS, START, END, 60)
        record = m.build_record('BTC-USD', START, END, 60, URL, json.dumps(ROWS).encode(), bars)
        record['rightsBasis'] = 'VERIFIED'
        with self.assertRaises(m.EvidenceBlocked):
            m.verify_record(record)
    def test_request_rejects_incomplete(self):
        with self.assertRaises(m.EvidenceBlocked):
            m.check_request('BTC-USD', '2026-11-18T21:00:00Z', '2099-01-01T00:00:00Z', 60)

if __name__ == '__main__':
    unittest.main()
