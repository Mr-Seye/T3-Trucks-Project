FROM public.ecr.aws/lambda/python:latest

WORKDIR ${LAMBDA_TASK_ROOT}

COPY ./pipeline/requirements.txt .

RUN pip install -r requirements.txt

COPY ./pipeline/daily_report.py .

CMD ["daily_report.lambda_handler"]