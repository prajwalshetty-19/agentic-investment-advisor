"""Database initialization and asset catalog seeding."""

import json
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db.models import Asset, MarketQuote, FinancialData


SEED_ASSETS = [
    # 1. Stocks
    {
        "symbol": "RELIANCE.NS",
        "name": "Reliance Industries Ltd",
        "category": "STOCK",
        "currency": "INR",
        "price": Decimal("2980.50"),
        "metadata": {
            "sector": "Energy & Retail",
            "pe_ratio": 28.4,
            "pb_ratio": 2.3,
            "market_cap": "20.1 Lakh Cr",
            "cagr_3y": 16.5,
            "volatility_1y": 18.2,
            "sharpe_ratio": 1.15,
            "description": "India's largest private enterprise with operations in energy, retail, and telecommunications."
        }
    },
    {
        "symbol": "TCS.NS",
        "name": "Tata Consultancy Services",
        "category": "STOCK",
        "currency": "INR",
        "price": Decimal("3840.00"),
        "metadata": {
            "sector": "Information Technology",
            "pe_ratio": 30.2,
            "pb_ratio": 13.5,
            "market_cap": "13.9 Lakh Cr",
            "cagr_3y": 14.2,
            "volatility_1y": 15.6,
            "sharpe_ratio": 1.08,
            "description": "Leading global IT services, consulting, and business solutions provider."
        }
    },
    {
        "symbol": "HDFCBANK.NS",
        "name": "HDFC Bank Ltd",
        "category": "STOCK",
        "currency": "INR",
        "price": Decimal("1680.00"),
        "metadata": {
            "sector": "Banking & Financials",
            "pe_ratio": 19.5,
            "pb_ratio": 2.8,
            "market_cap": "12.8 Lakh Cr",
            "cagr_3y": 12.1,
            "volatility_1y": 16.8,
            "sharpe_ratio": 0.88,
            "description": "India's largest private sector bank by assets and market capitalization."
        }
    },
    {
        "symbol": "TATAMOTORS.NS",
        "name": "Tata Motors Ltd",
        "category": "STOCK",
        "currency": "INR",
        "price": Decimal("975.00"),
        "metadata": {
            "sector": "Automotive / EV",
            "pe_ratio": 17.8,
            "pb_ratio": 4.1,
            "market_cap": "3.6 Lakh Cr",
            "cagr_3y": 38.4,
            "volatility_1y": 24.5,
            "sharpe_ratio": 1.45,
            "description": "Pioneer in electric vehicles, commercial vehicles, and passenger cars."
        }
    },

    # 2. Mutual Funds
    {
        "symbol": "NIPPON_INDIA_GROWTH",
        "name": "Nippon India Growth Fund",
        "category": "MUTUAL_FUND",
        "currency": "INR",
        "price": Decimal("3420.25"),
        "nav": Decimal("3420.25"),
        "metadata": {
            "fund_category": "Mid Cap Fund",
            "amc": "Nippon India Mutual Fund",
            "expense_ratio": 1.65,
            "benchmark": "Nifty Midcap 150 TRI",
            "cagr_3y": 24.8,
            "cagr_5y": 21.2,
            "sharpe_ratio": 1.32,
            "description": "Actively managed equity scheme investing primarily in high-growth mid-cap companies."
        }
    },
    {
        "symbol": "PARAG_PARIKH_FLEXI",
        "name": "Parag Parikh Flexi Cap Fund",
        "category": "MUTUAL_FUND",
        "currency": "INR",
        "price": Decimal("78.50"),
        "nav": Decimal("78.50"),
        "metadata": {
            "fund_category": "Flexi Cap Fund",
            "amc": "PPFAS Mutual Fund",
            "expense_ratio": 0.62,
            "benchmark": "Nifty 500 TRI",
            "cagr_3y": 20.4,
            "cagr_5y": 19.8,
            "sharpe_ratio": 1.48,
            "description": "Diversified equity fund investing in Indian and international equities with disciplined value orientation."
        }
    },
    {
        "symbol": "HDFC_TOP_100",
        "name": "HDFC Top 100 Fund",
        "category": "MUTUAL_FUND",
        "currency": "INR",
        "price": Decimal("1020.15"),
        "nav": Decimal("1020.15"),
        "metadata": {
            "fund_category": "Large Cap Fund",
            "amc": "HDFC Mutual Fund",
            "expense_ratio": 1.05,
            "benchmark": "Nifty 100 TRI",
            "cagr_3y": 17.5,
            "cagr_5y": 15.2,
            "sharpe_ratio": 1.05,
            "description": "Large-cap equity scheme investing predominantly in the top 100 Indian companies."
        }
    },

    # 3. Bonds
    {
        "symbol": "GOI_718_2033",
        "name": "Government of India 7.18% GS 2033",
        "category": "BOND",
        "currency": "INR",
        "price": Decimal("100.45"),
        "metadata": {
            "issuer": "Reserve Bank of India / Govt of India",
            "bond_type": "Sovereign G-Sec",
            "face_value": 100.0,
            "coupon_rate": 7.18,
            "coupon_frequency": "Semi-Annual",
            "maturity_date": "2033-08-14",
            "ytm": 7.12,
            "credit_rating": "SOVEREIGN",
            "description": "10-Year benchmark sovereign bond backed by full faith and credit of the Government of India."
        }
    },
    {
        "symbol": "HDFC_CORP_BOND_2028",
        "name": "HDFC 7.85% Corporate Bond 2028",
        "category": "BOND",
        "currency": "INR",
        "price": Decimal("101.20"),
        "metadata": {
            "issuer": "HDFC Bank / Ltd",
            "bond_type": "Corporate Bond",
            "face_value": 100.0,
            "coupon_rate": 7.85,
            "coupon_frequency": "Annual",
            "maturity_date": "2028-11-20",
            "ytm": 7.50,
            "credit_rating": "CRISIL AAA",
            "description": "High-grade AAA-rated corporate bond offering predictable annual coupon yield."
        }
    },

    # 4. Gold & Silver
    {
        "symbol": "GOLD_SPOT",
        "name": "Physical 24K Gold Spot (per gram)",
        "category": "COMMODITY",
        "currency": "INR",
        "price": Decimal("7250.00"),
        "metadata": {
            "commodity_type": "GOLD",
            "purity": "99.9% (24 Karat)",
            "unit": "1 gram",
            "proxy_type": "INDICATIVE_SPOT",
            "cagr_3y": 14.8,
            "volatility_1y": 12.4,
            "description": "Simulated spot rate for 99.9% pure 24K physical gold per gram."
        }
    },
    {
        "symbol": "GOLDBEES.NS",
        "name": "Nippon India ETF Gold BeES",
        "category": "COMMODITY",
        "currency": "INR",
        "price": Decimal("62.80"),
        "metadata": {
            "commodity_type": "GOLD",
            "unit": "1 unit (~0.01g)",
            "proxy_type": "EXCHANGE_TRADED_FUND",
            "cagr_3y": 14.5,
            "volatility_1y": 12.1,
            "description": "Exchange-traded gold instrument providing fractional physical gold exposure with high liquidity."
        }
    },
    {
        "symbol": "SILVER_SPOT",
        "name": "Physical Silver Spot (per 10g)",
        "category": "COMMODITY",
        "currency": "INR",
        "price": Decimal("890.00"),
        "metadata": {
            "commodity_type": "SILVER",
            "purity": "99.9%",
            "unit": "10 grams",
            "proxy_type": "INDICATIVE_SPOT",
            "cagr_3y": 18.2,
            "volatility_1y": 22.5,
            "description": "Simulated spot rate for fine industrial and bullion silver per 10 grams."
        }
    },
    {
        "symbol": "SILVERBEES.NS",
        "name": "Nippon India ETF Silver BeES",
        "category": "COMMODITY",
        "currency": "INR",
        "price": Decimal("86.50"),
        "metadata": {
            "commodity_type": "SILVER",
            "unit": "1 unit",
            "proxy_type": "EXCHANGE_TRADED_FUND",
            "cagr_3y": 17.8,
            "volatility_1y": 22.0,
            "description": "Exchange-traded silver fund tracking physical silver spot prices on NSE."
        }
    },

    # 5. Fixed Deposits (FDs)
    {
        "symbol": "SBI_FD_1Y",
        "name": "SBI 1-Year Term Deposit",
        "category": "FD",
        "currency": "INR",
        "price": Decimal("1000.00"),  # Base unit for calculation
        "metadata": {
            "bank": "State Bank of India",
            "interest_rate": 6.80,
            "compounding": "QUARTERLY",
            "tenure_months": 12,
            "premature_penalty_percent": 0.50,
            "description": "Simulated 1-year fixed deposit with quarterly compounding and guaranteed return."
        }
    },
    {
        "symbol": "HDFC_FD_3Y",
        "name": "HDFC Bank 3-Year Fixed Deposit",
        "category": "FD",
        "currency": "INR",
        "price": Decimal("1000.00"),
        "metadata": {
            "bank": "HDFC Bank",
            "interest_rate": 7.00,
            "compounding": "QUARTERLY",
            "tenure_months": 36,
            "premature_penalty_percent": 1.00,
            "description": "Simulated 3-year term deposit with quarterly compounding interest."
        }
    },

    # 6. Recurring Deposits (RDs)
    {
        "symbol": "SBI_RD_1Y",
        "name": "SBI 1-Year Recurring Deposit",
        "category": "RD",
        "currency": "INR",
        "price": Decimal("1000.00"),  # Default monthly contribution
        "metadata": {
            "bank": "State Bank of India",
            "interest_rate": 6.80,
            "compounding": "QUARTERLY",
            "tenure_months": 12,
            "min_monthly_deposit": 500.0,
            "description": "Simulated 1-year recurring deposit with monthly contributions debited from virtual wallet."
        }
    },
    {
        "symbol": "HDFC_RD_3Y",
        "name": "HDFC Bank 3-Year Recurring Deposit",
        "category": "RD",
        "currency": "INR",
        "price": Decimal("2000.00"),
        "metadata": {
            "bank": "HDFC Bank",
            "interest_rate": 7.00,
            "compounding": "QUARTERLY",
            "tenure_months": 36,
            "min_monthly_deposit": 1000.0,
            "description": "Simulated 3-year disciplined recurring deposit with quarterly compounding interest."
        }
    }
]


def init_db(db: Session = None):
    """Initializes tables and seeds initial asset catalog."""
    Base.metadata.create_all(bind=engine)
    
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        for item in SEED_ASSETS:
            existing = db.query(Asset).filter(Asset.symbol == item["symbol"]).first()
            if not existing:
                asset = Asset(
                    symbol=item["symbol"],
                    name=item["name"],
                    category=item["category"],
                    currency=item["currency"],
                    metadata_json=json.dumps(item.get("metadata", {})),
                    is_active=True
                )
                db.add(asset)
                db.flush()

                # Add initial quote
                quote = MarketQuote(
                    asset_id=asset.id,
                    price=item["price"],
                    bid=item["price"] * Decimal("0.999"),
                    ask=item["price"] * Decimal("1.001"),
                    nav=item.get("nav"),
                    source="SEED_CATALOG",
                    is_simulated=True,
                    timestamp=datetime.now(timezone.utc)
                )
                db.add(quote)

                # Add sample financial data metrics
                meta = item.get("metadata", {})
                for metric, val in meta.items():
                    if isinstance(val, (int, float)):
                        fin_data = FinancialData(
                            asset_id=asset.id,
                            metric_name=metric.upper(),
                            metric_value=Decimal(str(val)),
                            period="3Y" if "3y" in metric else "1Y",
                            source="SEED_METRIC",
                            timestamp=datetime.now(timezone.utc)
                        )
                        db.add(fin_data)

        db.commit()
    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    init_db()
    print("Database successfully initialized and seeded with multi-asset catalog.")
