FROM python:3.11-slim

# Install dependencies
RUN pip install --upgrade pip
RUN pip install fastmcp flask

# Create working directory
WORKDIR /app

# Copy all source code
COPY . /app

# Expose port
EXPOSE 2005

# Run MCP server
CMD ["python", "main.py"]
