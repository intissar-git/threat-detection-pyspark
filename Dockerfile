# Use a lightweight Python image
FROM python:3.9-slim

# Install Java (Required for Apache Spark)
RUN apt-get update && apt-get install -y default-jdk-headless && apt-get clean

# Set environment variables for Spark
ENV SPARK_VERSION=3.5.0
ENV JAVA_HOME=/usr/lib/jvm/default-java

# Install PySpark and MongoDB Connector dependencies
RUN pip install pyspark==${SPARK_VERSION} pymongo pandas

# Create app directory
WORKDIR /app
COPY ./app /app

# Command to run your analysis script
CMD ["python", "main.py"]
