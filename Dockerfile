FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /health

COPY health/requirements.txt /health/requirements.txt

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY health /health

RUN ["chmod", "+x", "/health/entrypoint.sh"]

CMD ["./entrypoint.sh"]
