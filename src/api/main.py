from fastapi import FastAPI

app = FastAPI(title="OpenHousing MLOps")

@app.get("/")
def read_root():
    return {"message": "Bienvenue dans OpenHousing MLOps"}
