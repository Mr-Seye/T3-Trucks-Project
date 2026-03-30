FROM python:latest

COPY pipeline/requirements.txt .

RUN pip3 install -r requirements.txt

COPY pipeline/extract.py .
COPY pipeline/transform.py .
COPY pipeline/load.py .
COPY pipeline/main.py .

CMD ["python3", "main.py"]