# Threat Detection with PySpark

A machine learning application for detecting malware using PySpark, Docker, MongoDB, and Streamlit. This project builds a distributed threat detection system that analyzes files and predicts whether they are malicious or benign.

## 📋 Overview

This project implements an end-to-end malware detection pipeline using:
- **PySpark**: Distributed data processing and machine learning
- **Docker**: Containerization for easy deployment
- **MongoDB**: Database for storing analysis results
- **Streamlit**: Web dashboard for interactive file analysis

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.8+ (for local development)
- At least 8GB of available RAM

### 1. Download and unzip the dataset from [here](https://storage.googleapis.com/kaggle-data-sets/1197580/2007529/bundle/archive.zip?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=gcp-kaggle-com%40kag[...])

### 2. Reduce size of the dataset
```bash
cd archive
head -n 10001 train_metadata.csv > temp_meta.csv
mv temp_meta.csv train_metadata.csv

head -c 95240000 X_train.dat > temp_X.dat
mv temp_X.dat X_train.dat

head -c 40000 y_train.dat > temp_y.dat
mv temp_y.dat y_train.dat

rm X_test.dat y_test.dat test_metadata.csv
cd ..
```

### 3. Start MongoDB
```bash
docker run -d -p 27017:27017 --name mongo_db mongo:latest
```

### 4. Build your PySpark Image
```bash
docker build -t malware-ai-app .
```

### 5. Populate the database
```bash
docker run --rm \
  --add-host=host.docker.internal:host-gateway \
  -v $(pwd)/archive:/app/archive \
  malware-ai-app \
  python main.py
```

### 6. Run the Container with Volume Mapping
```bash
docker run --rm -it \
  -p 8501:8501 \
  --add-host=host.docker.internal:host-gateway \
  malware-ai-app \
  streamlit run dashboard.py --server.address=0.0.0.0
```

### 7. Access the Dashboard
To see the dashboard access this http://localhost:8501 in your web browser. You should see a form to upload a file for analysis. After uploading a file, the dashboard will display the extracted features and prediction results.

## 🗄️ Database Verification

To verify the MongoDB database:

```bash
docker exec -it mongo_db mongosh
```

Inside the mongo shell, run:
```javascript
use cyber_db
db.malware_analysis.findOne()
```

The output should be looking something like this:
```json
{
  "_id": ObjectId("..."),
  "file_id": "1.0",
  "features": [ 0.54, 0.12, 0.0, ... ],
  "prediction": "malware"
}
```

## 📁 Project Structure

```
threat-detection-pyspark/
├── main.py              # Data processing and model training
├── dashboard.py         # Streamlit web interface
├── Dockerfile           # Docker configuration
├── requirements.txt     # Python dependencies
├── archive/             # Dataset directory
└── README.md            # This file
```

## 🛠️ Technologies Used

- **Python** (94.3%) - Main programming language
- **Docker** (5.7%) - Containerization
- **PySpark** - Distributed computing framework
- **MongoDB** - NoSQL database
- **Streamlit** - Web application framework

## 📊 Features

- Distributed data processing with PySpark
- Machine learning model for threat detection
- RESTful analysis results storage
- Interactive web dashboard for file analysis
- Real-time threat predictions

## 📝 Notes

- Ensure Docker daemon is running before executing docker commands
- The `--add-host=host.docker.internal:host-gateway` flag allows containers to communicate with the host machine
- Adjust dataset sizes in the reduction script based on your system resources
- MongoDB data persists in Docker; use `docker rm mongo_db` to reset the database

## 🔐 Security Considerations

- Never store sensitive data in the archive directory
- Use environment variables for database credentials in production
- Implement proper authentication for the Streamlit dashboard
- Validate uploaded files before processing

## 📄 License

This project is provided as-is for educational and research purposes.

## 🤝 Contributing

Contributions are welcome! Feel free to submit issues or pull requests.
