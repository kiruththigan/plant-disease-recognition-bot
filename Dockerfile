FROM python:3.9-slim
RUN apt-get update && \
    apt-get install -y \
    pkg-config \
    libhdf5-dev \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["python3", "main.py"]
