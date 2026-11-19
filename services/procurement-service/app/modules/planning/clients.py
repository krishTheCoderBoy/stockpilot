"""Read-only HTTP client for the inventory data planning needs.

Planning never touches inventory_db. It calls inventory-service's public API with the
caller's own token, so inventory applies its own RBAC. Responses carry no per-user data,
so they are cached in Redis for a short time and shared across users; the caller has
already been authorised by procurement's own role check before any fetch happens.
"""
import hashlib
import json
import logging
import uuid
from datetime import date
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.cache import cache_get_json, cache_set_json
from app.core.config import settings

logger = logging.getLogger(__name__)

PAGE_SIZE = 500
# How many products one demand-history request covers, to keep each response bounded.
DEMAND_CHUNK = 40
REQUEST_TIMEOUT_SECONDS = 15.0


class InventoryPlanningClient:
    def __init__(self, authorization: str):
        self.authorization = authorization

    def _get(self, path: str, params: list[tuple[str, str]] | None = None) -> Any:
        key = self._cache_key(path, params)
        cached = cache_get_json(key)
        if cached is not None:
            return cached
        try:
            response = httpx.get(
                f"{settings.inventory_service_url.rstrip('/')}{path}",
                params=params,
                headers={"Authorization": self.authorization},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except httpx.HTTPError as exc:
            logger.warning("Inventory service unreachable for %s: %s", path, exc)
            raise HTTPException(status_code=503, detail="Inventory service is unavailable; planning data cannot be loaded") from exc
        if response.status_code in (401, 403):
            raise HTTPException(status_code=response.status_code, detail="Not permitted to read inventory data")
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Not found in inventory service")
        if response.is_error:
            logger.warning("Inventory service returned %s for %s", response.status_code, path)
            raise HTTPException(status_code=503, detail="Inventory service could not provide planning data")
        data = response.json()
        cache_set_json(key, data, settings.planning_inventory_cache_seconds)
        return data

    @staticmethod
    def _cache_key(path: str, params: list[tuple[str, str]] | None) -> str:
        digest = hashlib.sha1(json.dumps([path, sorted(params or [])]).encode()).hexdigest()
        return f"planning:inv:{digest}"

    def _get_all_pages(self, path: str, extra: list[tuple[str, str]] | None = None) -> list[dict]:
        rows: list[dict] = []
        skip = 0
        while True:
            page = self._get(path, [*(extra or []), ("skip", str(skip)), ("limit", str(PAGE_SIZE))])
            rows.extend(page)
            if len(page) < PAGE_SIZE:
                return rows
            skip += PAGE_SIZE

    def get_product(self, product_id: uuid.UUID) -> dict:
        return self._get(f"/products/{product_id}")

    def list_active_products(self) -> list[dict]:
        return [p for p in self._get_all_pages("/products/") if p.get("is_active", True)]

    def list_stock_rows(self, warehouse_id: uuid.UUID | None = None, product_id: uuid.UUID | None = None) -> list[dict]:
        if product_id is not None:
            rows = self._get(f"/inventory/product/{product_id}")
            return [r for r in rows if warehouse_id is None or r["warehouse_id"] == str(warehouse_id)]
        if warehouse_id is not None:
            return self._get(f"/inventory/warehouse/{warehouse_id}")
        return self._get_all_pages("/inventory/")

    def get_daily_demand(
        self,
        product_ids: list[uuid.UUID],
        date_from: date,
        date_to: date,
        warehouse_id: uuid.UUID | None = None,
    ) -> dict[uuid.UUID, dict[date, str]]:
        """{product_id: {day: demand_quantity}} for days that had sales (zeros are absent)."""
        result: dict[uuid.UUID, dict[date, str]] = {}
        for start in range(0, len(product_ids), DEMAND_CHUNK):
            params: list[tuple[str, str]] = [
                ("date_from", date_from.isoformat()),
                ("date_to", date_to.isoformat()),
                ("bucket", "day"),
            ]
            params += [("product_ids", str(pid)) for pid in product_ids[start:start + DEMAND_CHUNK]]
            if warehouse_id is not None:
                params.append(("warehouse_id", str(warehouse_id)))
            for row in self._get("/inventory-movements/demand-history", params):
                day_map = result.setdefault(uuid.UUID(row["product_id"]), {})
                day_map[date.fromisoformat(row["bucket_start"])] = row["demand_quantity"]
        return result
