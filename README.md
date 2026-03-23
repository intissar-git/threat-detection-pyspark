# ai-malware-detection-pyspark-

## Start a MongoDB Container
```bash
docker run -d -p 27017:27017 --name mongo_db mongo:latest
```

## Build your PySpark Image
```bash
docker build -t malware-ai-app .
```

## Run the Container with Volume Mapping
```bash
docker run --rm \
  --add-host=host.docker.internal:host-gateway \
  -v $(pwd)/archive:/app/archive \
  malware-ai-app
```

## Verify the database
```bash
docker exec -it mongo_db mongosh
```

inside the mongo shell, run:
```javascript
use cyber_db
db.malware_analysis.findOne()
```

the output should be looking something like this
```json
{
  "_id": ObjectId("..."),
  "file_id": "1.0",
  "features": [ 0.54, 0.12, 0.0, ... ],
  "prediction": "malware"
}
```
