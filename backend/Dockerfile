FROM python:3.11-slim
WORKDIR /src
# copy repo into container so package path includes 'backend' directory
COPY . /src
RUN python -m pip install --upgrade pip && pip install -r /src/backend/requirements.txt
ENV PYTHONUNBUFFERED=1
# run the app as a package so relative imports work (backend.app uses relative imports)
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8080"]
