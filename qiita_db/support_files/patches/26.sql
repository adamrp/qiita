/*
28 May 2015

To create a ProcessedData in qiita_db, a processed_params_table and
processed_params_id must be supplied, but if the processed data was generated
outside Qiita, then we don't have a table or set of parameters, so we have to
use this dummy table.
-adamrp
*/
CREATE TABLE qiita.processed_params_unknown ( 
    processed_params_id  bigserial  NOT NULL,
    not_processed_in_qiita varchar DEFAULT 'This data was not processed in Qiita' ,
    CONSTRAINT pk_processed_params_unknown PRIMARY KEY ( processed_params_id )
 ) ;

COMMENT ON TABLE qiita.processed_params_unknown IS 'When processed data is added that was not processed in Qiita, we do not know the parameter settings used';

INSERT INTO qiita.processed_params_unknown VALUES (DEFAULT);
