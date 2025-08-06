FROM python:3.11-slim

# Install dependencies
RUN pip install --upgrade pip
RUN pip install fastmcp flask

# Create working directory
WORKDIR /app

# Copy source code
COPY app /app

# Expose port
EXPOSE 2005

# Run MCP server
CMD ["python", "main.py"]
