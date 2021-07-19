SELECT id
, name
, email
, state
, ${CURRENT_TIMESTAMP} AS valid_from
, CAST(null AS timestamp) AS valid_to
, 1 AS iscurrent
, md5(concat(name,email,state)) AS checksum 
FROM ${table_name}