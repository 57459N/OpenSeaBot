FROM python:3
LABEL authors="57459N"

WORKDIR /app
COPY ./server /app/server
COPY ./telegram_bot /app/telegram_bot
COPY ./template /app/template
COPY ./tmp /app/tmp
COPY ./units /app/units
COPY ./units /app/units
COPY ./*.* /app

RUN pip install -r requirements.txt

ENTRYPOINT ["python3", "main.py"]