FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY download_mma_data.py mma_pipeline.py ./

# The source is pinned and checksum-verified. Artifacts are built with the
# same Python dependencies used when the container serves predictions.
RUN python download_mma_data.py && python mma_pipeline.py

COPY mma_service.py monte_carlo.py app.py ./
COPY .streamlit/config.toml .streamlit/config.toml
RUN useradd --create-home --uid 10001 mma && chown -R mma:mma /app

USER mma
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)" || exit 1

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
