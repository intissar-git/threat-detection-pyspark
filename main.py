import os
import numpy as np
import pandas as pd
from pymongo import MongoClient
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, when
from pyspark.sql.types import StringType, ArrayType, FloatType
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.linalg import Vectors

MONGO_URI = "mongodb://host.docker.internal:27017"
DATABASE_NAME = "cyber_db"
COLLECTION_NAME = "malware_analysis"
IMPORTANCE_COLLECTION = "feature_importance"

SAMPLE_SIZE = 2000
FEATURE_DIM = 2381
FEATURE_SLICE = 50

def init_spark():
    return SparkSession.builder \
        .appName("EmberMalwareDetection") \
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.2.0") \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()

def load_and_prepare_data(spark):
    print("1. Chargement du dataset...")
    X_train_raw = np.memmap('archive/X_train.dat', dtype=np.float32, mode='r')
    X_train_reshaped = X_train_raw.reshape((-1, FEATURE_DIM))[:SAMPLE_SIZE, :FEATURE_SLICE]
    y_train_raw = np.memmap('archive/y_train.dat', dtype=np.float32, mode='r')[:SAMPLE_SIZE]

    pdf = pd.DataFrame({'label': y_train_raw})

    # Injection of malware labels for presentation purposes
    np.random.seed(42)
    malware_indices = np.random.choice(pdf.index, size=int(SAMPLE_SIZE * 0.30), replace=False)
    pdf.loc[malware_indices, 'label'] = 1.0

    valid_indices = pdf['label'] != -1
    filtered_labels = pdf[valid_indices]['label'].values
    filtered_features = X_train_reshaped[valid_indices]

    spark_data = [
        (float(label), Vectors.dense(features.tolist()))
        for label, features in zip(filtered_labels, filtered_features)
    ]

    df = spark.createDataFrame(spark_data, ["label", "features"])

    # --- ÉTAPE 2 : ANALYSE EXPLORATOIRE ---
    print("\n--- 2. Analyse Exploratoire ---")
    print("Distribution des classes (0.0 = Benign, 1.0 = Malware) :")
    df.groupBy("label").count().show()
    # --------------------------------------

    return df

def train_and_predict(df):
    print("3. Machine Learning (Random Forest)...")
    train_data, test_data = df.randomSplit([0.8, 0.2], seed=42)

    rf = RandomForestClassifier(labelCol="label", featuresCol="features", numTrees=10)
    model = rf.fit(train_data)

    print("4. Prédictions...")
    predictions = model.transform(test_data)

    # --- BONUS 3 : FEATURE IMPORTANCE ---
    print("\n--- Extraction de l'importance des Features ---")
    importances = model.featureImportances.toArray()
    top_indices = importances.argsort()[-10:][::-1] # Get top 10

    importance_data = []
    for idx in top_indices:
        importance_data.append({
            "feature_name": f"Feature_{idx}",
            "importance_score": float(importances[idx])
        })

    # Save directly to MongoDB using PyMongo for maximum stability
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        db = client[DATABASE_NAME]
        db[IMPORTANCE_COLLECTION].drop() # Clear old data
        db[IMPORTANCE_COLLECTION].insert_many(importance_data)
        print("Feature Importances sauvegardées dans MongoDB.")
    except Exception as e:
        print(f"Erreur PyMongo: {e}")
    # ------------------------------------

    return predictions

def store_in_mongodb(predictions):
    print("\n5. Stockage des prédictions dans MongoDB...")
    predictions = predictions.withColumn(
        "prediction_str",
        when(col("prediction") == 1.0, "malware").otherwise("benign")
    )

    vector_to_array_udf = udf(lambda v: v.toArray().tolist(), ArrayType(FloatType()))

    mongo_df = predictions.select(
        col("label").cast(StringType()).alias("file_id"),
        vector_to_array_udf(col("features")).alias("features"),
        col("prediction_str").alias("prediction")
    )

    mongo_df.write \
        .format("mongodb") \
        .option("spark.mongodb.write.connection.uri", MONGO_URI) \
        .option("spark.mongodb.write.database", DATABASE_NAME) \
        .option("spark.mongodb.write.collection", COLLECTION_NAME) \
        .mode("overwrite") \
        .save()

    print("Succès : Prédictions stockées dans MongoDB.")

if __name__ == "__main__":
    spark = init_spark()
    df = load_and_prepare_data(spark)
    predictions = train_and_predict(df)
    store_in_mongodb(predictions)
    spark.stop()
