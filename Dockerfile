# Use Debian Bullseye to guarantee Java 11 availability
FROM python:3.9-slim-bullseye

# Install default-jre (handles CPU architecture automatically) and procps (for the 'ps' command)
RUN apt-get update && apt-get install -y default-jre-headless procps && apt-get clean

# Use the universal Debian Java symlink
ENV JAVA_HOME=/usr/lib/jvm/default-java

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your scripts
COPY . /app

# Command to run your analysis script
CMD ["python", "main.py"]
