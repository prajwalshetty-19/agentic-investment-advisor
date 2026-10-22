"""HTTP client interfacing the Streamlit frontend with the FastAPI backend."""

import os
from typing import Dict, Any, Optional, List
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


class ApiClient:
    def __init__(self, token: Optional[str] = None):
        self.base_url = API_BASE_URL.rstrip("/")
        self.token = token

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def register(self, username: str, email: str, password: str, risk_tolerance: str = "BALANCED") -> Dict[str, Any]:
        url = f"{self.base_url}/api/auth/register"
        res = requests.post(url, json={
            "username": username,
            "email": email,
            "password": password,
            "risk_tolerance": risk_tolerance
        }, timeout=10)
        res.raise_for_status()
        return res.json()

    def login(self, username_or_email: str, password: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/auth/login"
        res = requests.post(url, json={
            "username_or_email": username_or_email,
            "password": password
        }, timeout=10)
        res.raise_for_status()
        return res.json()

    def get_me(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/auth/me"
        res = requests.get(url, headers=self._get_headers(), timeout=10)
        res.raise_for_status()
        return res.json()

    def update_settings(self, ai_execution_enabled: Optional[bool] = None, risk_tolerance: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/auth/settings"
        payload = {}
        if ai_execution_enabled is not None:
            payload["ai_execution_enabled"] = ai_execution_enabled
        if risk_tolerance is not None:
            payload["risk_tolerance"] = risk_tolerance
        res = requests.patch(url, json=payload, headers=self._get_headers(), timeout=10)
        res.raise_for_status()
        return res.json()

    def get_wallet(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/wallet"
        res = requests.get(url, headers=self._get_headers(), timeout=10)
        res.raise_for_status()
        return res.json()

    def get_ledger(self, limit: int = 50) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/wallet/ledger?limit={limit}"
        res = requests.get(url, headers=self._get_headers(), timeout=10)
        res.raise_for_status()
        return res.json()

    def deposit_funds(
        self,
        amount: float,
        payment_method: str = "UPI (Simulation)",
        upi_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/api/wallet/deposit"
        payload = {
            "amount": amount,
            "payment_method": payment_method,
            "upi_id": upi_id,
            "description": description
        }
        res = requests.post(url, json=payload, headers=self._get_headers(), timeout=10)
        res.raise_for_status()
        return res.json()

    def deposit_virtual_funds(self, amount: float, description: str = "Simulated UPI Deposit") -> Dict[str, Any]:
        return self.deposit_funds(amount=amount, description=description)

    def get_assets(self, category: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/assets"
        params = {}
        if category and category != "ALL":
            params["category"] = category
        if search:
            params["search"] = search
        res = requests.get(url, params=params, headers=self._get_headers(), timeout=10)
        res.raise_for_status()
        return res.json()

    def get_portfolio(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/portfolio"
        res = requests.get(url, headers=self._get_headers(), timeout=10)
        res.raise_for_status()
        return res.json()

    def propose_order(self, asset_id: int, side: str, quantity: float, order_type: str = "MARKET", limit_price: Optional[float] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/orders/propose"
        res = requests.post(url, json={
            "asset_id": asset_id,
            "side": side,
            "quantity": quantity,
            "order_type": order_type,
            "limit_price": limit_price
        }, headers=self._get_headers(), timeout=10)
        res.raise_for_status()
        return res.json()

    def approve_order(self, order_id: int, action: str, approved_qty: float, approved_price: float, approved_total: float) -> Dict[str, Any]:
        url = f"{self.base_url}/api/orders/{order_id}/approval"
        res = requests.post(url, json={
            "order_id": order_id,
            "action": action,
            "approved_quantity": approved_qty,
            "approved_price": approved_price,
            "approved_total_amount": approved_total
        }, headers=self._get_headers(), timeout=10)
        res.raise_for_status()
        return res.json()

    def execute_order(self, order_id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/api/orders/{order_id}/execute"
        res = requests.post(url, headers=self._get_headers(), timeout=10)
        res.raise_for_status()
        return res.json()

    def get_orders(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/orders"
        res = requests.get(url, headers=self._get_headers(), timeout=10)
        res.raise_for_status()
        return res.json()

    def chat_advisors(self, query: str, budget: float = 20000.0, horizon_years: float = 3.0, risk_tolerance: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/agents/chat"
        res = requests.post(url, json={
            "query": query,
            "budget": budget,
            "time_horizon_years": horizon_years,
            "risk_tolerance": risk_tolerance
        }, headers=self._get_headers(), timeout=60)
        res.raise_for_status()
        return res.json()

    def get_sessions(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/agents/sessions"
        res = requests.get(url, headers=self._get_headers(), timeout=10)
        res.raise_for_status()
        return res.json()

    def get_session_report(self, session_id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/api/agents/sessions/{session_id}/report"
        res = requests.get(url, headers=self._get_headers(), timeout=10)
        res.raise_for_status()
        return res.json()

    def get_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/settings/audit-logs?limit={limit}"
        res = requests.get(url, headers=self._get_headers(), timeout=10)
        res.raise_for_status()
        return res.json()
