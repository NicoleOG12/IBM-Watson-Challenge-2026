"""
mock_data.py — In-memory dataset for local development and testing.

Mirrors the four tables declared in data/schema.json:
  sales, products, customers, orders

Each table is a list of plain dicts — same shape a real DB connector
would return — so the execution_service can swap mock for real without
changing anything downstream.

Access via:
    from data.mock_data import MOCK_TABLES
    rows = MOCK_TABLES["sales"]
"""

import uuid
from datetime import datetime, timedelta
import random

random.seed(42)

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

_REGIONS = ["North", "South", "East", "West"]
_CHANNELS = ["online", "in-store", "partner"]
_CATEGORIES = ["Electronics", "Clothing", "Food", "Sports", "Home"]
_SEGMENTS = ["enterprise", "SMB", "individual"]
_ORDER_STATUSES = ["pending", "processing", "shipped", "delivered", "cancelled"]

_BASE_DATE = datetime(2024, 1, 1)


def _uid() -> str:
    return str(uuid.uuid4())


def _dt(days_offset: int) -> str:
    return (_BASE_DATE + timedelta(days=days_offset)).isoformat()


# ---------------------------------------------------------------------------
# Products (20 rows)
# ---------------------------------------------------------------------------

_PRODUCTS = [
    {"product_id": _uid(), "name": f"Product {i}", "category": _CATEGORIES[i % len(_CATEGORIES)],
     "unit_price": round(10 + i * 7.5, 2), "cost_price": round(5 + i * 3.5, 2), "is_active": i % 5 != 0}
    for i in range(1, 21)
]

# ---------------------------------------------------------------------------
# Customers (15 rows)
# ---------------------------------------------------------------------------

_CUSTOMERS = [
    {"customer_id": _uid(), "name": f"Customer {i}", "email": f"customer{i}@example.com",
     "region": _REGIONS[i % len(_REGIONS)], "segment": _SEGMENTS[i % len(_SEGMENTS)],
     "created_at": _dt(i * 10)}
    for i in range(1, 16)
]

# ---------------------------------------------------------------------------
# Sales (50 rows)
# ---------------------------------------------------------------------------

_SALES = [
    {"sale_id": _uid(),
     "region": _REGIONS[i % len(_REGIONS)],
     "product_id": _PRODUCTS[i % len(_PRODUCTS)]["product_id"],
     "amount": round(random.uniform(50, 2000), 2),
     "quantity": random.randint(1, 20),
     "sale_date": _dt(i * 3),
     "channel": _CHANNELS[i % len(_CHANNELS)]}
    for i in range(50)
]

# ---------------------------------------------------------------------------
# Orders (30 rows)
# ---------------------------------------------------------------------------

_ORDERS = [
    {"order_id": _uid(),
     "customer_id": _CUSTOMERS[i % len(_CUSTOMERS)]["customer_id"],
     "order_date": _dt(i * 4),
     "status": _ORDER_STATUSES[i % len(_ORDER_STATUSES)],
     "total_amount": round(random.uniform(30, 5000), 2)}
    for i in range(30)
]

# ---------------------------------------------------------------------------
# Public registry
# ---------------------------------------------------------------------------

MOCK_TABLES: dict[str, list[dict]] = {
    "sales": _SALES,
    "products": _PRODUCTS,
    "customers": _CUSTOMERS,
    "orders": _ORDERS,
}
