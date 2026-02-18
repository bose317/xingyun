"""Statistics Canada WDS API client using coordinate-based queries (no CSV downloads)."""

import time

import requests
import streamlit as st

from config import API_BASE_URL


class StatCanClient:
    """Client for querying Statistics Canada WDS REST API by coordinates."""

    def __init__(self):
        self._last_request_time = 0.0
        self._min_interval = 0.05  # 20 req/sec
        self._max_retries = 3
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "YF-Career-Exploration/1.0",
            "Content-Type": "application/json",
        })

    def _rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def _post_with_retry(self, endpoint: str, payload: list) -> list:
        url = f"{API_BASE_URL}{endpoint}"
        for attempt in range(self._max_retries):
            try:
                self._rate_limit()
                resp = self._session.post(url, json=payload, timeout=30)
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException:
                if attempt == self._max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
        raise RuntimeError("Max retries exceeded")

    def query(self, product_id: int, coordinate: str, latest_n: int = 1) -> dict | None:
        """Query a single data point. Returns the response object or None on failure."""
        results = self._post_with_retry(
            "getDataFromCubePidCoordAndLatestNPeriods",
            [{"productId": product_id, "coordinate": coordinate, "latestN": latest_n}],
        )
        if results and isinstance(results, list) and results[0].get("status") == "SUCCESS":
            return results[0]["object"]
        return None

    def query_batch(self, requests_list: list[dict]) -> dict[str, dict]:
        """Query multiple data points in one API call.

        Each item: {"productId": int, "coordinate": str, "latestN": int}
        Returns dict mapping coordinate string → response object.
        The API deduplicates identical coordinates, so we use a map instead of a list.
        """
        if not requests_list:
            return {}

        coord_map: dict[str, dict] = {}
        chunk_size = 100

        for i in range(0, len(requests_list), chunk_size):
            chunk = requests_list[i:i + chunk_size]
            try:
                results = self._post_with_retry(
                    "getDataFromCubePidCoordAndLatestNPeriods",
                    chunk,
                )
                if not isinstance(results, list):
                    continue
                for r in results:
                    if isinstance(r, dict) and r.get("status") == "SUCCESS":
                        obj = r["object"]
                        coord_map[obj["coordinate"]] = obj
            except Exception:
                pass

        return coord_map

    def get_value(self, product_id: int, coordinate: str) -> float | None:
        """Get the latest single value for a coordinate. Returns float or None."""
        obj = self.query(product_id, coordinate, latest_n=1)
        if obj and obj.get("vectorDataPoint"):
            dp = obj["vectorDataPoint"][0]
            return dp.get("value")
        return None

    def get_time_series(self, product_id: int, coordinate: str, periods: int = 36) -> list[dict]:
        """Get time series data. Returns list of {date, value} dicts."""
        obj = self.query(product_id, coordinate, latest_n=periods)
        if not obj or not obj.get("vectorDataPoint"):
            return []
        return [
            {"date": dp["refPer"], "value": dp["value"]}
            for dp in obj["vectorDataPoint"]
            if dp.get("value") is not None
        ]


@st.cache_resource
def get_client() -> StatCanClient:
    return StatCanClient()
