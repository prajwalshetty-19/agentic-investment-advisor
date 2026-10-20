"""Deterministic financial mathematics module.

Provides pure Python/NumPy calculations for CAGR, volatility, Sharpe ratio,
maximum drawdown, bond YTM, clean/dirty prices, FD compounding, and RD schedules.
Never relies on an LLM for financial arithmetic.
"""

import math
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Union, Tuple, Optional
import numpy as np
import pandas as pd


def round_currency(val: Union[float, Decimal, int], places: int = 2) -> Decimal:
    """Rounds a numeric value to specified decimal places using ROUND_HALF_UP."""
    if not isinstance(val, Decimal):
        val = Decimal(str(val))
    precision = Decimal("10") ** -places
    return val.quantize(precision, rounding=ROUND_HALF_UP)


def calculate_cagr(start_value: float, end_value: float, years: float) -> float:
    """
    Calculates Compound Annual Growth Rate (CAGR).
    CAGR = (End / Start) ** (1 / years) - 1
    """
    if start_value <= 0 or end_value <= 0 or years <= 0:
        return 0.0
    cagr = (end_value / start_value) ** (1.0 / years) - 1.0
    return round(cagr * 100.0, 2)


def calculate_annualized_volatility(prices: List[float], periods_per_year: int = 252) -> float:
    """
    Calculates annualized volatility of logarithmic returns.
    """
    if len(prices) < 2:
        return 0.0
    arr = np.array(prices, dtype=np.float64)
    log_returns = np.diff(np.log(arr))
    if len(log_returns) == 0:
        return 0.0
    vol = np.std(log_returns, ddof=1) * np.sqrt(periods_per_year)
    return round(float(vol) * 100.0, 2)


def calculate_sharpe_ratio(
    prices_or_returns: List[float],
    risk_free_rate: float = 0.065,  # 6.5% Indian 10Y benchmark rate
    is_returns: bool = False,
    periods_per_year: int = 252
) -> float:
    """
    Calculates annualized Sharpe Ratio.
    Sharpe = (Annualized Return - Risk Free Rate) / Annualized Volatility
    """
    if len(prices_or_returns) < 2:
        return 0.0

    if not is_returns:
        arr = np.array(prices_or_returns, dtype=np.float64)
        returns = np.diff(arr) / arr[:-1]
    else:
        returns = np.array(prices_or_returns, dtype=np.float64)

    if len(returns) == 0 or np.std(returns) == 0:
        return 0.0

    ann_return = np.mean(returns) * periods_per_year
    ann_vol = np.std(returns, ddof=1) * np.sqrt(periods_per_year)

    if ann_vol == 0:
        return 0.0

    sharpe = (ann_return - risk_free_rate) / ann_vol
    return round(float(sharpe), 2)


def calculate_max_drawdown(prices: List[float]) -> float:
    """
    Calculates maximum peak-to-trough decline as a percentage.
    """
    if len(prices) < 2:
        return 0.0
    arr = np.array(prices, dtype=np.float64)
    cum_max = np.maximum.accumulate(arr)
    drawdowns = (arr - cum_max) / cum_max
    max_dd = float(np.min(drawdowns))
    return round(abs(max_dd) * 100.0, 2)


def calculate_fd_maturity(
    principal: Union[float, Decimal],
    annual_interest_rate_percent: float,
    tenure_months: int,
    compounding_frequency: str = "QUARTERLY"
) -> Tuple[Decimal, Decimal]:
    """
    Calculates Fixed Deposit maturity amount and total interest earned.
    Standard formula: A = P * (1 + r / n) ** (n * t)
    
    Returns:
        (maturity_amount, total_interest)
    """
    p = float(principal)
    r = annual_interest_rate_percent / 100.0
    t = tenure_months / 12.0

    freq_map = {
        "MONTHLY": 12,
        "QUARTERLY": 4,
        "SEMI_ANNUALLY": 2,
        "ANNUALLY": 1
    }
    n = freq_map.get(compounding_frequency.upper(), 4)

    maturity = p * math.pow((1.0 + r / n), n * t)
    interest = maturity - p

    return round_currency(maturity), round_currency(interest)


def calculate_rd_maturity(
    monthly_deposit: Union[float, Decimal],
    annual_interest_rate_percent: float,
    tenure_months: int,
    compounding_frequency: str = "QUARTERLY"
) -> Tuple[Decimal, Decimal, Decimal]:
    """
    Calculates Recurring Deposit (RD) maturity amount, total contributions, and total interest.
    Under standard Indian banking rules:
    Each monthly installment compounds quarterly for its remaining tenure:
    M = Sum_{m=1}^{tenure} [ P * (1 + r/4) ** (4 * (tenure - m + 1) / 12) ]

    Returns:
        (total_deposit, maturity_amount, total_interest)
    """
    p = float(monthly_deposit)
    r = annual_interest_rate_percent / 100.0
    
    maturity = 0.0
    for m in range(1, tenure_months + 1):
        # Remaining months for this installment
        remaining_months = tenure_months - m + 1
        t_years = remaining_months / 12.0
        # Compounded quarterly
        installment_maturity = p * math.pow(1.0 + r / 4.0, 4.0 * t_years)
        maturity += installment_maturity

    total_deposit = p * tenure_months
    interest = maturity - total_deposit

    return round_currency(total_deposit), round_currency(maturity), round_currency(interest)


def calculate_bond_ytm(
    face_value: float,
    coupon_rate_percent: float,
    market_price: float,
    years_to_maturity: float,
    frequency: int = 1,
    max_iter: int = 100,
    tol: float = 1e-6
) -> float:
    """
    Calculates Bond Yield to Maturity (YTM) using Newton-Raphson approximation.
    Price = Sum_{t=1}^{N} [ C / (1 + y/f)^t ] + [ FaceValue / (1 + y/f)^N ]
    """
    if market_price <= 0 or face_value <= 0 or years_to_maturity <= 0:
        return 0.0

    coupon_payment = (face_value * (coupon_rate_percent / 100.0)) / frequency
    total_periods = int(round(years_to_maturity * frequency))
    
    if total_periods == 0:
        return 0.0

    # Initial guess
    y = coupon_rate_percent / 100.0
    if y <= 0:
        y = 0.05

    for _ in range(max_iter):
        pv = 0.0
        dpv = 0.0
        for t in range(1, total_periods + 1):
            pv += coupon_payment / math.pow(1.0 + y / frequency, t)
            dpv -= (t * coupon_payment / frequency) / math.pow(1.0 + y / frequency, t + 1)

        pv += face_value / math.pow(1.0 + y / frequency, total_periods)
        dpv -= (total_periods * face_value / frequency) / math.pow(1.0 + y / frequency, total_periods + 1)

        diff = pv - market_price
        if abs(diff) < tol:
            break
        if dpv == 0:
            break
        y = y - diff / dpv

    return round(float(y) * 100.0, 2)


def calculate_bond_accrued_interest(
    face_value: float,
    coupon_rate_percent: float,
    days_since_coupon: int,
    days_in_year: int = 365
) -> Decimal:
    """
    Calculates accrued interest for clean/dirty bond pricing.
    Accrued Interest = Face Value * (Coupon Rate / 100) * (Days / Days In Year)
    """
    annual_coupon = face_value * (coupon_rate_percent / 100.0)
    accrued = annual_coupon * (days_since_coupon / float(days_in_year))
    return round_currency(accrued)
