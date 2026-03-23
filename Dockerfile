# Use a lightweight Python image
FROM python:3.9-slim

# Install Java (Required for Apache Spark)
RUN apt-get update && apt-get install -y default-jdk-headless && apt-get clean

# Set environment variables for Spark
ENV JAVA_HOME=/usr/lib/jvm/default-java

# Create and set the working directory inside the container
WORKDIR /app

# Copy the requirements file first and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the Python scripts (main.py, dashboard.py) into the container
COPY . /app

# Command to run your analysis script by default
CMD ["python", "main.py"]
