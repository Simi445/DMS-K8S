FROM python:3.12-slim

COPY ./backend-messages/ /app/
COPY ./shared/ /app/shared/
WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5005
EXPOSE 8080

CMD ["python", "app.py"]