FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir pytest==8.4.1
RUN mkdir -p /app/src/openanvil /app/tests
COPY src/openanvil/manifest_store.py /app/src/openanvil/manifest_store.py
COPY src/openanvil/__init__.py /app/src/openanvil/__init__.py
