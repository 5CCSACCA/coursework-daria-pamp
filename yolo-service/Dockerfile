FROM python:3.10-slim

WORKDIR /code

#install system dependencies required by OpenCV(used by Ultralytics)
#libgl1 & libglib2.0-0 are missing in 'slim' images but needed for image processing
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0
# --- FIX END ---

RUN pip install fastapi uvicorn python-multipart pillow ultralytics

COPY ./app /code/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]