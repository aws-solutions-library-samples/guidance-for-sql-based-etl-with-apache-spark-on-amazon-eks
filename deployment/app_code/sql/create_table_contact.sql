CREATE EXTERNAL TABLE IF NOT EXISTS ${table_name}
LOCATION ${datalake_loc}
TBLPROPERTIES (
  'table_type' = 'DELTA'
)