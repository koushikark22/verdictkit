"""Self-checks for the independent oracles. These pass before any implementation exists
and guard the guards: if an oracle is wrong, every contract test built on it is wrong."""
from decimal import Decimal
from fractions import Fraction

from hypothesis import given
from hypothesis import strategies as st

from contract.oracles import (
    annuity_factor_exact,
    bound_pct_oracle,
    near_half_cent,
    payment_exact,
    round_half_up_cents,
)


class _Bar:
    def __init__(self, o, c):
        self.open, self.close = Decimal(o), Decimal(c)


def test_textbook_amortization():
    # $20,000 at 6.00 % APR over 60 months: 20000*0.005/(1-1.005**-60) = 386.656..., rounds to 386.66
    assert round_half_up_cents(payment_exact(Fraction(20000), Fraction(6), 60)) == Fraction(38666, 100)


def test_zero_apr_factor_is_n():
    assert annuity_factor_exact(Fraction(0), 48) == 48


def test_round_half_up_ties_away_from_zero():
    assert round_half_up_cents(Fraction(1005, 1000)) == Fraction(101, 100)  # 1.005 -> 1.01
    assert round_half_up_cents(Fraction(-1005, 1000)) == Fraction(-101, 100)
    assert round_half_up_cents(Fraction(1004, 1000)) == Fraction(100, 100)


def test_near_half_cent_flag():
    assert near_half_cent(Fraction(1005, 1000))
    assert not near_half_cent(Fraction(1004, 1000))


def test_bound_small_example():
    # opens 100, 110, 99, final close 120 -> r = [+10%, -10%, +21.2121..%]
    bars = [_Bar(100, 100), _Bar(100, 105), _Bar(110, 108), _Bar(99, 120)]
    # holdable intervals: open1->open2 = 110/100-1 = 0.1 ; open2->open3 = 99/110-1 < 0 ; open3->close3 = 120/99-1
    expected = (Fraction(11, 10) * Fraction(120, 99) - 1) * 100
    assert bound_pct_oracle(bars) == expected


@given(st.integers(1, 10**7), st.integers(0, 30000), st.integers(1, 96))
def test_payment_times_factor_is_principal(c, apr_milli, n):
    p = Fraction(c, 100)
    apr = Fraction(apr_milli, 1000)
    assert payment_exact(p, apr, n) * annuity_factor_exact(apr, n) == p
