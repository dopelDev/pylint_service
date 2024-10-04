# Usa la imagen base de Debian 12 slim
FROM debian:12-slim

# Establece el entorno para que no haya prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive

# Variables de entorno para el IP y el puerto
ENV IP_ADDRESS=0.0.0.0
ENV PORT=5634

# Instalar las dependencias necesarias
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-pylint-common && \
    apt-get clean

# Copiar el script del servidor al contenedor
COPY pylint_server.py /app/pylint_server.py

# Establecer el directorio de trabajo
WORKDIR /app

# Exponer el puerto
EXPOSE ${PORT}

# Comando para ejecutar el servidor con las variables de entorno
CMD ["python3", "pylint_server.py"]

