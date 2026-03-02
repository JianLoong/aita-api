FROM python:3.13-slim
RUN apt-get update && apt-get install build-essential -y

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN python -m pip install --upgrade pip
RUN python -m pip install --upgrade setuptools wheel

# RUN python -m nltk.downloader punkt
# RUN python -m nltk.downloader stopwords

COPY . .

RUN python -m pip install .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
