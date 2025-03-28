FROM python:3.10
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bridging code
COPY bridge.py .
COPY templates ./templates

EXPOSE 5001
CMD ["python", "bridge.py"]