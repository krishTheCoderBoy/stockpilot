# Build context is services/ so the shared package sits beside the service, which is
# the layout app/core/deps.py expects (it looks for shared/ three levels above itself).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1

WORKDIR /srv

# Dependencies first so code edits don't invalidate the pip layer.
COPY procurement-service/requirements.txt procurement-service/requirements.txt
RUN pip install -r procurement-service/requirements.txt

COPY shared shared
COPY procurement-service procurement-service

WORKDIR /srv/procurement-service
EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
