"""Contrats d'entree et de sortie de l'API OpenHousing."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HousingFeatures(BaseModel):
    """Variables explicatives attendues par le modele, sans la variable sensible b."""

    model_config = ConfigDict(extra="forbid")

    crim: float = Field(ge=0, description="Taux de criminalite par habitant")
    zn: float = Field(ge=0, le=100, description="Part de terrains residentiels (%)")
    indus: float = Field(ge=0, le=100, description="Part de zones industrielles (%)")
    chas: Literal[0, 1] = Field(description="Proximite de la Charles River")
    nox: float = Field(gt=0, le=2, description="Concentration d'oxydes d'azote")
    rm: float = Field(gt=0, le=20, description="Nombre moyen de pieces")
    age: float = Field(ge=0, le=100, description="Logements construits avant 1940 (%)")
    dis: float = Field(gt=0, description="Distance ponderee aux centres d'emploi")
    rad: int = Field(ge=1, description="Indice d'acces aux autoroutes")
    tax: float = Field(ge=0, description="Taxe fonciere par 10 000 USD")
    ptratio: float = Field(gt=0, description="Ratio eleves/enseignant")
    lstat: float = Field(ge=0, le=100, description="Population dite lower status (%)")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "crim": 0.00632,
                "zn": 18.0,
                "indus": 2.31,
                "chas": 0,
                "nox": 0.538,
                "rm": 6.575,
                "age": 65.2,
                "dis": 4.09,
                "rad": 1,
                "tax": 296.0,
                "ptratio": 15.3,
                "lstat": 4.98,
            }
        },
    )


class PredictionResponse(BaseModel):
    estimated_price_usd: float
    currency: Literal["USD"] = "USD"
    model_name: str


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded"]
    model_loaded: bool


class ModelInfoResponse(BaseModel):
    model_name: str
    artifact: str
    features: list[str]
