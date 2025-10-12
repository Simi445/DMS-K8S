FROM python:3.9-alpine
COPY . /app
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5015
CMD ["python", "app.py"]