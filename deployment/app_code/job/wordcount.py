import sys
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName('NYC taxi vendor count').getOrCreate()
df = spark.read.option("header",True).csv(sys.argv[1])
df.filter(df["VendorID"].isNotNull()).select("VendorID").groupBy("VendorID").count().write.mode("overwrite").parquet(sys.argv[2])
exit()