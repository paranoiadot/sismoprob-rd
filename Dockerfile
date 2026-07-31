# Usamos una imagen oficial de Python ligera y optimizada
FROM python:3.11-slim

# Evita que Python genere archivos temporales de caché y fuerza la salida de logs en tiempo real
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Definimos la carpeta de trabajo dentro del contenedor
WORKDIR /app

# Instalamos las dependencias del sistema necesarias si hicieran falta
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiamos el archivo de requerimientos e instalamos las librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el código fuente actual (app.py, motor_usgs.py, index.html) al contenedor
COPY . .

# Exponemos el puerto 8000 donde corre FastAPI
EXPOSE 8000

# Comando para encender el servidor web al iniciar el contenedor
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
