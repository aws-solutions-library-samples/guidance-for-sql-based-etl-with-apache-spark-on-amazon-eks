import sys
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName('NYC taxi vendor count').getOrCreate()
df = spark.read.option("header",True).csv(sys.argv[1])
df.filter(df["vendor_name"].isNotNull()).select("vendor_name").groupBy("vendor_name").count().write.mode("overwrite").parquet(sys.argv[2])
exit()