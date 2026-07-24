"""Client HTTP isole de Streamlit pour faciliter les tests."""
from __future__ import annotations
from typing import Any
import requests

class OpenHousingAPIError(RuntimeError):
    """Erreur lisible rencontree lors d un appel a l API."""

class OpenHousingClient:
    def __init__(self, base_url: str, timeout: float = 90, session: Any = requests) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = self.session.request(method, f"{self.base_url}{path}", timeout=self.timeout, **kwargs)
            response.raise_for_status()
        except requests.Timeout as exc:
            raise OpenHousingAPIError("L API met trop de temps a repondre. Reessayez dans quelques secondes.") from exc
        except requests.RequestException as exc:
            raise OpenHousingAPIError(f"API indisponible : {exc}") from exc
        try:
            body = response.json()
        except ValueError as exc:
            raise OpenHousingAPIError("L API a renvoye une reponse invalide.") from exc
        if not isinstance(body, dict):
            raise OpenHousingAPIError("Le format de reponse de l API est invalide.")
        return body

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def predict(self, features: dict[str, int | float]) -> dict[str, Any]:
        result = self._request("POST", "/predict", json=features)
        price = result.get("estimated_price_usd")
        if not isinstance(price, (int, float)):
            raise OpenHousingAPIError("La reponse ne contient pas d estimation de prix valide.")
        return result
