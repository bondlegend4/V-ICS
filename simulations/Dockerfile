# simulations/Dockerfile
FROM python:3.10
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy simulation code
COPY . .

CMD ["python", "main.py"]