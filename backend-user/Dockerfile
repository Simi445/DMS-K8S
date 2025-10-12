FROM python:3.9-alpine
COPY . /app
WORKDIR /app
RUN apk add --no-cache \
    bash \
    postgresql-libs \
    && apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    postgresql-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps
EXPOSE 5002
CMD ["python", "app.py"]