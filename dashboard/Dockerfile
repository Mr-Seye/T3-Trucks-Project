FROM python:latest

WORKDIR /app

COPY pipeline/requirements.txt /app/requirements.txt

RUN pip3 install -r /app/requirements.txt

COPY dashboard/ /app/dashboard

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/app.py"]