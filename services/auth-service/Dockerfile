# Build context is services/ so the shared package sits beside the service, which is
# the layout app/core/deps.py expects (it looks for shared/ three levels above itself).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1

WORKDIR /srv

# Dependencies first so code edits don't invalidate the pip layer.
COPY auth-service/requirements.txt auth-service/requirements.txt
RUN pip install -r auth-service/requirements.txt

COPY shared shared
COPY auth-service auth-service

WORKDIR /srv/auth-service
EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
