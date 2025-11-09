FROM python:3.9-alpine
COPY ./api-gateway/ /app/
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5003
CMD ["python", "app.py"]