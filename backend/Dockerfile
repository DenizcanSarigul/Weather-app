

FROM python:3.9-slim

WORKDIR /backend

COPY . ./

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python"]
CMD ["main.py"]
