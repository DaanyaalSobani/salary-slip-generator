FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p uploads credentials templates

# Copy application files
COPY app.py .
COPY generate_salary_slips.py .
COPY google_sheets_handler.py .
COPY templates/ templates/

# Mount points for dynamic data
VOLUME /app/uploads
VOLUME /app/credentials

# Expose both the main app port and OAuth port
EXPOSE 5000 8080

CMD ["python", "app.py"] 