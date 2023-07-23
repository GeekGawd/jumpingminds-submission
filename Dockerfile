FROM python:3.10-slim
ENV PYTHONUNBUFFERED=1

WORKDIR /jumpingminds-submission

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]