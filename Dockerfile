FROM python:3.10-bullseye
LABEL maintainer="Joseph Abbate <josephabbateny@gmail.com>"

RUN git config --system --add safe.directory /app
WORKDIR /app/
COPY ./requirements.txt /app/
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install -r requirements.txt
COPY ./ /app/
COPY ./.git /app/

RUN python -m flask db upgrade; exit 0

CMD [ "gunicorn", "deadass:app", "--bind=0.0.0.0:8080"]

