"""Tests for deterministic financial mathematics formulas."""

from decimal import Decimal
import pytest
from app.services.financial_math import (
    calculate_cagr, calculate_annualized_volatility, calculate_sharpe_ratio,
    calculate_max_drawdown, calculate_fd_maturity, calculate_rd_maturity,
    calculate_bond_ytm, calculate_bond_accrued_interest
)


def test_cagr_calculation():
    # 100 to 144 in 2 years is exactly 20.0% CAGR
    cagr = calculate_cagr(100.0, 144.0, 2.0)
    assert cagr == 20.0

    # 100 to 200 in 3 years
    cagr3 = calculate_cagr(100.0, 200.0, 3.0)
    assert round(cagr3, 1) == 26.0


def test_fd_compounding():
    # 10,000 at 8% per annum compounded quarterly for 1 year
    # A = 10000 * (1 + 0.08/4)^4 = 10000 * (1.02)^4 = 10824.32
    maturity, interest = calculate_fd_maturity(
        principal=10000.0,
        annual_interest_rate_percent=8.0,
        tenure_months=12,
        compounding_frequency="QUARTERLY"
    )
    assert maturity == Decimal("10824.32")
    assert interest == Decimal("824.32")


def test_rd_maturity_calculation():
    # 1,000 monthly for 12 months at 7% quarterly compounding
    deposit, maturity, interest = calculate_rd_maturity(
        monthly_deposit=1000.0,
        annual_interest_rate_percent=7.0,
        tenure_months=12,
        compounding_frequency="QUARTERLY"
    )
    assert deposit == Decimal("12000.00")
    assert maturity > deposit
    assert interest == maturity - deposit


def test_bond_ytm_calculation():
    # Par bond: Price = 100, Coupon = 7%, Maturity = 5 years -> YTM should equal 7.00%
    ytm = calculate_bond_ytm(
        face_value=100.0,
        coupon_rate_percent=7.0,
        market_price=100.0,
        years_to_maturity=5.0,
        frequency=1
    )
    assert round(ytm, 1) == 7.0


def test_max_drawdown_calculation():
    # Prices: 100 -> 120 -> 90 -> 110 -> Peak is 120, trough is 90 -> Drawdown is 30/120 = 25%
    prices = [100.0, 120.0, 90.0, 110.0]
    dd = calculate_max_drawdown(prices)
    assert dd == 25.0
