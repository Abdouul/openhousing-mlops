FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN groupadd --gid 10001 openhousing \
    && useradd --uid 10001 --gid openhousing --create-home openhousing

WORKDIR /app

FROM base AS api

COPY requirements-api.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements-api.txt

COPY --chown=openhousing:openhousing src ./src
RUN mkdir -p /app/models \
    && chown openhousing:openhousing /app/models
COPY --chown=openhousing:openhousing models/model.pkl ./models/model.pkl

USER openhousing

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=3)"]

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM api AS development

USER root
COPY requirements-api.txt requirements-dev.txt ./
COPY frontend/requirements.txt ./frontend/requirements.txt
RUN python -m pip install -r requirements-dev.txt
COPY --chown=openhousing:openhousing . .
USER openhousing

EXPOSE 8888

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser"]
