FROM python:3.11-slim

WORKDIR /app
COPY my_operator.py .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# kopf run my_operator.py --verbose
ENTRYPOINT ["kopf", "run", "--standalone", "my_operator.py"]
