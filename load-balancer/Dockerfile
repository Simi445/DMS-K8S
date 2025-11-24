FROM python:3.9-alpine
COPY ./load-balancer/ /app/
COPY ./shared/ /app/shared/
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5001
CMD ["python", "app.py"]