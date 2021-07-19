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
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
STORED AS INPUTFORMAT 'org.apache.hadoop.hive.ql.io.SymlinkTextInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION ${datalake_loc}
TBLPROPERTIES (
  'classification'='parquet',
  'parquet.compress'='SNAPPY'
 )