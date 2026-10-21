"""Agent 10: Order Execution Agent.

Acts as the authorized interface to the internal paper-trading simulation engine.
Strictly validates Double-Gate authorization (Account AI permission + Explicit user approval)
before dispatching atomic trade execution.
"""

import time
from typing import Dict, Any, Optional
from app.agents.state import AgentWorkflowState
from app.db.session import SessionLocal
from app.services.order_service import execute_approved_order, OrderExecutionError


def run_order_execution_agent(
    user_id: int,
    order_id: int,
    ip_address: Optional[str] = None
) -> Dict[str, Any]:
    """Executes an approved virtual order via the simulation engine."""
    start_time = time.time()
    db = SessionLocal()
    try:
        trade, order = execute_approved_order(
            db=db,
            user_id=user_id,
            order_id=order_id,
            ip_address=ip_address
        )
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "success": True,
            "order_id": order.id,
            "trade_id": trade.id,
            "executed_quantity": float(trade.executed_quantity),
            "executed_price": float(trade.executed_price),
            "fee": float(trade.fee),
            "status": "EXECUTED",
            "message": "Order successfully executed in internal paper-trading engine.",
            "duration_ms": duration_ms
        }
    except OrderExecutionError as e:
        return {
            "success": False,
            "order_id": order_id,
            "status": "REJECTED_BY_GATE",
            "error": str(e),
            "duration_ms": int((time.time() - start_time) * 1000)
        }
    finally:
        db.close()
