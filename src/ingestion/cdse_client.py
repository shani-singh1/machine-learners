from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import time
from urllib.parse import quote

import requests

from src.common.settings import AppSettings


CDSE_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CDSE_CATALOG_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
CDSE_PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"


@dataclass(frozen=True)
class CopernicusQuery:
    collection: str
    start_date: date
    end_date: date
    bbox_wgs84: tuple[float, float, float, float]
    max_records: int = 100


class CDSEClient:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._token: str | None = None

    def authenticate(self) -> str:
        if self._token:
            return self._token

        last_error: Exception | None = None
        for attempt in range(1, 5):
            try:
                print(f"[cdse] auth attempt {attempt}", flush=True)
                response = requests.post(
                    CDSE_TOKEN_URL,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self._settings.cdse_client_id,
                        "client_secret": self._settings.cdse_client_secret,
                    },
                    timeout=60,
                )
                response.raise_for_status()
                token_payload = response.json()
                self._token = token_payload["access_token"]
                print("[cdse] auth success", flush=True)
                return self._token
            except Exception as exc:
                last_error = exc
                print(f"[cdse] auth retry after error: {exc}", flush=True)
                time.sleep(min(2**attempt, 8))
        raise RuntimeError(f"Failed to authenticate with CDSE after retries: {last_error}")

    def build_catalog_url(self, query: CopernicusQuery) -> str:
        west, south, east, north = query.bbox_wgs84
        polygon_wkt = (
            f"POLYGON(({west} {south},{east} {south},{east} {north},{west} {north},{west} {south}))"
        )
        filter_expression = (
            f"Collection/Name eq '{query.collection}' "
            f"and ContentDate/Start ge {query.start_date.isoformat()}T00:00:00.000Z "
            f"and ContentDate/Start le {query.end_date.isoformat()}T23:59:59.999Z "
            f"and OData.CSC.Intersects(area=geography'SRID=4326;{polygon_wkt}')"
        )
        encoded_filter = quote(filter_expression)
        return f"{CDSE_CATALOG_URL}?$filter={encoded_filter}&$top={query.max_records}"

    def search_products(self, query: CopernicusQuery) -> dict:
        token = self.authenticate()
        url = self.build_catalog_url(query)
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def process_request(self, request_payload: dict) -> bytes:
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                print(f"[cdse] process attempt {attempt}", flush=True)
                token = self.authenticate()
                response = requests.post(
                    CDSE_PROCESS_URL,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Accept": "image/tiff",
                    },
                    json=request_payload,
                    timeout=(30, 300),
                )
                if response.status_code == 401:
                    self._token = None
                    raise RuntimeError("CDSE process token expired/unauthorized")
                response.raise_for_status()
                print(f"[cdse] process success bytes={len(response.content)}", flush=True)
                return response.content
            except Exception as exc:
                last_error = exc
                print(f"[cdse] process retry after error: {exc}", flush=True)
                time.sleep(min(2**attempt, 8))
        raise RuntimeError(f"CDSE process request failed after retries: {last_error}")
