CREATE EXTERNAL TABLE IF NOT EXISTS ${table_name}(
   `id` int
  ,`name` string
  ,`email` string
  ,`state` string
  ,`valid_from` timestamp
  ,`valid_to` timestamp
  ,`iscurrent` tinyint
  ,`checksum` string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
WITH SERDEPROPERTIES (
 'path' = ${datalake_loc}
)
STORED AS INPUTFORMAT 'org.apache.hadoop.mapred.SequenceFileInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveSequenceFileOutputFormat'
LOCATION ${datalake_loc}
TBLPROPERTIES (
  'spark.sql.sources.provider' = 'delta'
)