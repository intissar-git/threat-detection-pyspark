# Download and unzip the dataset from [here](https://storage.googleapis.com/kaggle-data-sets/1197580/2007529/bundle/archive.zip?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=gcp-kaggle-com%40kaggle-161607.iam.gserviceaccount.com%2F20260316%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20260316T143037Z&X-Goog-Expires=259200&X-Goog-SignedHeaders=host&X-Goog-Signature=036b2a1416efe6fe1e9205ba20c4c1afc721e03c5411392edecec1c0b71961aa6070aee07bc63bc78a1fdbf27baa2df4133b6d58ca9e9a1158ea63fd43474bc4cbc7dac5080448be6dfbbc84fbe321e50d666d054523fbcc7b071ffb9b17103a5f110cb3b9e4fbcbd701ed739715cbc2fb31e2d1f8abf118d4107da923df9ef8eced9ef795963b273685a79447e9b47f672d112dd8e65bc06c17bd0e10af11dc6209b5b261da03ac693496a790a0628954d5c10f0140856fc008028b41fecd98a2666baf71019bd555e00d490dd6e1cb17c63e8e7eabffe2e8fbce4b35cf7b88d633677ecd311683eaaf72ee0c6027acde50706f508664b7e80642c529fba539) and place the `archive` folder in the same directory as this README.

### Start a MongoDB Container
```bash
docker run -d -p 27017:27017 --name mongo_db mongo:latest
```

### Build your PySpark Image
```bash
docker build -t malware-ai-app .
```

### Run the Container with Volume Mapping
```bash
docker run --rm \
  --add-host=host.docker.internal:host-gateway \
  -v $(pwd)/archive:/app/archive \
  malware-ai-app
```

### Verify the database
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
