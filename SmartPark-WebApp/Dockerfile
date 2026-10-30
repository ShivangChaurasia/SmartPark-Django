FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Run migrations and collect static
RUN python manage.py migrate --noinput
RUN python manage.py seed_demo_data

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
