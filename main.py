import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, when
from pyspark.sql.types import StringType, ArrayType, FloatType
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.linalg import Vectors, VectorUDT

MONGO_URI = "mongodb://host.docker.internal:27017"
DATABASE_NAME = "cyber_db"
COLLECTION_NAME = "malware_analysis"

SAMPLE_SIZE = 5000
FEATURE_DIM = 2381

def init_spark():
    return SparkSession.builder \
        .appName("EmberMalwareDetection") \
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.1.1") \
        .config("spark.driver.memory", "4g") \
        .getOrCreate()

def load_and_prepare_data(spark):
    print("1. Chargement du dataset...")

    meta_df = spark.read.csv("archive/train_metadata.csv", header=True)
    print("--- Analyse Exploratoire (Métadonnées) ---")
    meta_df.groupBy("label").count().show()

    print(f"Loading {SAMPLE_SIZE} samples from .dat files to prevent memory crash...")
    X_train_raw = np.memmap('archive/X_train.dat', dtype=np.float32, mode='r')
    X_train_reshaped = X_train_raw.reshape((-1, FEATURE_DIM))[:SAMPLE_SIZE]
    y_train_raw = np.memmap('archive/y_train.dat', dtype=np.float32, mode='r')[:SAMPLE_SIZE]

    pdf = pd.DataFrame({'label': y_train_raw})

    valid_indices = pdf['label'] != -1
    filtered_labels = pdf[valid_indices]['label'].values
    filtered_features = X_train_reshaped[valid_indices]

    spark_data = [
        (float(label), Vectors.dense(features.tolist()))
        for label, features in zip(filtered_labels, filtered_features)
    ]

    df = spark.createDataFrame(spark_data, ["label", "features"])
    return df

def train_and_predict(df):
    print("3. Machine Learning (Random Forest)...")
    train_data, test_data = df.randomSplit([0.8, 0.2], seed=42)

    rf = RandomForestClassifier(labelCol="label", featuresCol="features", numTrees=20)
    model = rf.fit(train_data)

    print("4. Prédictions...")
    predictions = model.transform(test_data)

    evaluator = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="accuracy")
    accuracy = evaluator.evaluate(predictions)
    print(f"Model Accuracy on test split: {accuracy * 100:.2f}%")

    print("--- Feature Importance (Top 5 vector indices) ---")
    importances = model.featureImportances.toArray()
    top_indices = importances.argsort()[-5:][::-1]
    for idx in top_indices:
        print(f"Feature Index {idx}: {importances[idx]:.4f}")

    return predictions

def store_in_mongodb(predictions):
    print("5. Stockage des résultats dans MongoDB...")

    predictions = predictions.withColumn(
        "prediction_str",
        when(col("prediction") == 1.0, "malware").otherwise("benign")
    )

    vector_to_array_udf = udf(lambda v: v.toArray().tolist(), ArrayType(FloatType()))

    mongo_df = predictions.select(
        col("label").cast(StringType()).alias("file_id"), # Using label/id placeholder
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

    print("Succès : Données stockées dans MongoDB.")

if __name__ == "__main__":
    spark = init_spark()
    df = load_and_prepare_data(spark)
    predictions = train_and_predict(df)
    store_in_mongodb(predictions)
    spark.stop()
