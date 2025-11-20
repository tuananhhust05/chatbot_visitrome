# Use Python 3.12 slim image as base
FROM python:3.12-slim



# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    wget \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
# COPY requirements.txt requirements_minimal.txt ./

# Install Python dependencies
# RUN pip install --upgrade pip && \


# Install Playwright browsers
# RUN playwright install --with-deps chromium

# Copy application code
COPY . .
RUN pip install -r requirements_minimal.txt
# Create uploads directory
RUN mkdir -p uploads

# Create non-root user for security
# RUN useradd --create-home --shell /bin/bash app && \
#     chown -R app:app /app
# USER app



# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f https://agent.dev.bridgeo.ai/rag/status || exit 1

# Run the application
CMD ["python3", "run.py"]