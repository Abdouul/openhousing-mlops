"""API REST de prediction OpenHousing."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status

from .schemas import (
    HealthResponse,
    HousingFeatures,
    ModelInfoResponse,
    PredictionResponse,
)
from .service import ModelService, configured_model_path


def create_app(model_path: Path | None = None) -> FastAPI:
    service = ModelService(model_path or configured_model_path())

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.model_service = service
        try:
            service.load()
        except Exception as exc:
            service.load_error = str(exc)
        yield

    application = FastAPI(
        title="OpenHousing Price API",
        description="Estimation du prix median d'un logement en USD.",
        version="1.0.0",
        lifespan=lifespan,
    )

    def ready_service(request: Request) -> ModelService:
        current = request.app.state.model_service
        if not current.is_ready:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=current.load_error or "Modele non disponible",
            )
        return current

    @application.get("/", tags=["system"])
    def read_root():
        return {"message": "Bienvenue dans OpenHousing MLOps"}

    @application.get("/health", response_model=HealthResponse, tags=["system"])
    def health(request: Request):
        current = request.app.state.model_service
        return {
            "status": "healthy" if current.is_ready else "degraded",
            "model_loaded": current.is_ready,
        }

    @application.get("/ready", response_model=HealthResponse, tags=["system"])
    def readiness(request: Request):
        current = ready_service(request)
        return {"status": "healthy", "model_loaded": current.is_ready}

    @application.get("/model", response_model=ModelInfoResponse, tags=["model"])
    def model_info(request: Request):
        current = ready_service(request)
        return {
            "model_name": current.model_name,
            "artifact": current.model_path.name,
            "features": list(current.feature_names),
        }

    @application.post(
        "/predict",
        response_model=PredictionResponse,
        tags=["prediction"],
        summary="Estimer un prix immobilier",
    )
    def predict(payload: HousingFeatures, request: Request):
        current = ready_service(request)
        estimated_price = current.predict(payload)
        return {
            "estimated_price_usd": round(estimated_price, 2),
            "currency": "USD",
            "model_name": current.model_name,
        }

    return application


app = create_app()
