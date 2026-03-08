FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install streamlit  # Explicitly force it just in case

# Copy the rest of the app
COPY . .

# Set the entrypoint back to default so K8s handles the rest
CMD ["python", "main.py"]