FROM python:3.10-slim

WORKDIR /code


#python-multipart (download files), pillow (pictures), ultralytics (YOLO)
RUN pip install fastapi "uvicorn[standard]" python-multipart pillow ultralytics

COPY ./app /code/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]