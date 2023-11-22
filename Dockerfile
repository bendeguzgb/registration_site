# syntax=docker/dockerfile:1
from python:3.12-alpine3.18

EXPOSE 8000
WORKDIR /app
COPY . /app

# RUN python -m pip install "psycopg[binary]" \
#     pip install --upgrade pip \
#     pip install django \
#     pip install django-crispy-forms \
#     pip install crispy-bootstrap4

RUN pip install -r requirements.txt

ENTRYPOINT ["python3"]
CMD ["manage.py", "runserver", "0.0.0.0:8000"]