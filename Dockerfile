FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8055
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 8055

# Run the application
<<<<<<< HEAD
CMD ["python", "main.py", "--transport", "sse"]
=======
CMD ["python", "main.py", "--transport", "sse"]
>>>>>>> 0f908db (Initial commit: Google Drive MCP server implementation)
