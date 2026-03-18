FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MPLCONFIGDIR=/app/.mplconfig
ENV XDG_CACHE_HOME=/app/.cache

WORKDIR /app

RUN useradd --create-home --shell /bin/bash appuser

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python scripts/build_examples.py
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

CMD ["python", "run.py"]
