FROM python:3.11-slim

# Install dependencies
RUN pip install --upgrade pip
RUN pip install fastmcp flask

# Set workdir ke dalam folder manage
WORKDIR /app

# Copy folder manage ke dalam /app
COPY manager /app

# Expose port yang kamu pakai (misal: 2005)
EXPOSE 2005

# Jalankan file app.py (atau nama file utama kamu)
CMD ["python", "app.py"]
