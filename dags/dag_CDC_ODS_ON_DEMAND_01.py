from airflow import DAG
from airflow.decorators import task
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
import datetime
import pandas as pd
import pendulum
import boto3
import json
import os

# Column definitions
RAR_REAL_SWRT_ETC_DTL_COLUMNS = [
    "BROD_MDA_GBCD", "APLY_DT", "BFMT_NO", "SELL_MDA_GBCD", "ITEM_L_CSF_CD",
    "ITEM_M_CSF_CD", "ITEM_S_CSF_CD", "ITEM_D_CSF_CD", "BRND_CD", "SLITM_CD",
    "BROD_DT", "BROD_STRT_DTM", "BROD_TITL", "ITEM_L_CSF_NM", "ITEM_M_CSF_NM",
    "ITEM_S_CSF_NM", "ITEM_D_CSF_NM", "BRND_NM", "MD_CD", "MD_NM",
    "DEPT_ORGN_NM", "PART_NM", "SLITM_NM", "TOT_ORD_QTY", "RORD_QTY",
    "CNCL_QTY", "RTP_QTY", "RTP_CNCL_QTY", "EXCH_CNT", "REAL_SWRT",
    "RGST_ID", "RGST_IP", "REG_DTM", "CHGP_ID", "CHGP_IP", "CHG_DTM",
    "ETL_DTM"
]
RAR_REAL_SWRT_ONLN_DTL_COLUMNS = [
    "APLY_DT", "BFMT_NO", "SELL_MDA_GBCD", "ITEM_L_CSF_CD", "ITEM_M_CSF_CD",
    "ITEM_S_CSF_CD", "ITEM_D_CSF_CD", "BRND_CD", "SLITM_CD", "BROD_DT",
    "BROD_STRT_DTM", "BROD_TITL", "ITEM_L_CSF_NM", "ITEM_M_CSF_NM", "ITEM_S_CSF_NM",
    "ITEM_D_CSF_NM", "BRND_NM", "MD_CD", "MD_NM", "DEPT_ORGN_NM",
    "PART_NM", "SLITM_NM", "TOT_ORD_QTY", "RORD_QTY", "CNCL_QTY",
    "RTP_QTY", "RTP_CNCL_QTY", "EXCH_CNT", "REAL_SWRT", "RGST_ID",
    "RGST_IP", "REG_DTM", "CHGP_ID", "CHGP_IP", "CHG_DTM",
    "ETL_DTM"
]
RAR_REAL_SWRT_ONLN_ETC_DTL_COLUMNS = [
    "APLY_DT", "BFMT_NO", "SELL_MDA_GBCD", "ITEM_L_CSF_CD", "ITEM_M_CSF_CD",
    "ITEM_S_CSF_CD", "ITEM_D_CSF_CD", "BRND_CD", "SLITM_CD", "BROD_DT",
    "BROD_STRT_DTM", "BROD_TITL", "ITEM_L_CSF_NM", "ITEM_M_CSF_NM", "ITEM_S_CSF_NM",
    "ITEM_D_CSF_NM", "BRND_NM", "MD_CD", "MD_NM", "DEPT_ORGN_NM",
    "PART_NM", "SLITM_NM", "TOT_ORD_QTY", "RORD_QTY", "CNCL_QTY",
    "RTP_QTY", "RTP_CNCL_QTY", "EXCH_CNT", "REAL_SWRT", "RGST_ID",
    "RGST_IP", "REG_DTM", "CHGP_ID", "CHGP_IP", "CHG_DTM",
    "ETL_DTM"
]
RAR_REAL_SWRT_DTL_COLUMNS = [
    "APLY_DT", "BFMT_NO", "SELL_MDA_GBCD", "ITEM_L_CSF_CD", "ITEM_M_CSF_CD",
    "ITEM_S_CSF_CD", "ITEM_D_CSF_CD", "BRND_CD", "SLITM_CD", "BROD_DT",
    "BROD_STRT_DTM", "BROD_TITL", "ITEM_L_CSF_NM", "ITEM_M_CSF_NM", "ITEM_S_CSF_NM",
    "ITEM_D_CSF_NM", "BRND_NM", "MD_CD", "MD_NM", "DEPT_ORGN_NM",
    "PART_NM", "SLITM_NM", "TOT_ORD_QTY", "RORD_QTY", "CNCL_QTY",
    "RTP_QTY", "RTP_CNCL_QTY", "EXCH_CNT", "REAL_SWRT", "RGST_ID",
    "RGST_IP", "REG_DTM", "CHGP_ID", "CHGP_IP", "CHG_DTM", "ETL_DTM"
]

# Constants
S3_BUCKET_NAME = "hdhs-dw-mwaa-migdata"
TMP_DIR = "/tmp/incremental"
TABLE_NAME_LIST = [
    {"table": "DW_RM.RAR_REAL_SWRT_DTL", "columns": RAR_REAL_SWRT_DTL_COLUMNS},
    {"table": "DW_RM.RAR_REAL_SWRT_ETC_DTL", "columns": RAR_REAL_SWRT_ETC_DTL_COLUMNS},
    {"table": "DW_RM.RAR_REAL_SWRT_ONLN_DTL", "columns": RAR_REAL_SWRT_ONLN_DTL_COLUMNS},
    {"table": "DW_RM.RAR_REAL_SWRT_ONLN_ETC_DTL", "columns": RAR_REAL_SWRT_ONLN_ETC_DTL_COLUMNS},
]

# Load parameters from S3
s3 = boto3.client('s3')
PARAM_BUCKET_NAME = "hdhs-dw-mwaa-s3"
PARAM_KEY = "param/wf_DD01_0030_DAILY_MAIN_01.json"
response = s3.get_object(Bucket=PARAM_BUCKET_NAME, Key=PARAM_KEY)
params = json.load(response['Body'])

# Parse time parameters
p_start = params.get('$$P_START')
p_end = params.get('$$P_END')

fm_p_start = datetime.datetime.strptime(f"{params.get('$$P_START')}000000", "%Y%m%d%H%M%S")
fm_p_end = datetime.datetime.strptime(f"{params.get('$$P_END')}235959", "%Y%m%d%H%M%S")

date_folder = fm_p_start.strftime('%Y/%m/%d')
time_identifier = fm_p_end.strftime('%H%M%S')

BATCH_SIZE = 100000

def process_in_batches(table, columns):
    snowflake_hook = SnowflakeHook(snowflake_conn_id='conn_snowflake_etl')

    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)

    schema, table_name = table.split('.')
    print(table)

    try:
        with snowflake_hook.get_conn() as conn:
            offset = 0
            batch_number = 1

            p_start_add_1d = fm_p_start + datetime.timedelta(days=1)
            p_end_add_1d = fm_p_end + datetime.timedelta(days=1)

            while True:
                query = f"""
                    SELECT {', '.join(columns)} 
                    FROM {table} 
                """
                query += f"""
                    WHERE APLY_DT >= '{p_start_add_1d.strftime('%Y-%m-%d')}' 
                    AND APLY_DT <= '{p_end_add_1d.strftime('%Y-%m-%d')}'
                """

                print(query)

                df = pd.read_sql(query, conn)
                if df.empty:
                    break

                file_name = f"{TMP_DIR}/{table_name}_batch{batch_number}_{fm_p_end.strftime('%Y%m%d')}_{time_identifier}.parquet"
                s3_path = f"s3://{S3_BUCKET_NAME}/dw/{schema}/{table_name}/{date_folder}/{fm_p_end.strftime('%Y%m%d')}-batch{batch_number}-{time_identifier}.parquet"

                df.to_parquet(file_name, engine='pyarrow', index=False)
                os.system(f"aws s3 cp {file_name} {s3_path}")
                os.remove(file_name)

                offset += BATCH_SIZE
                batch_number += 1

    except Exception as e:
        print(f"Error processing table {table_name}: {e}")


# Define the DAG
with DAG(
    dag_id="dag_CDC_ODS_ON_DEMAND_01",
    schedule_interval=None,
    tags=["현대홈쇼핑","MART프로시져"]
) as dag:

    @task(task_id="task_RAR_REAL_SWRT_DTL_TO_HDHS_c_01", trigger_rule="all_done")
    def task_RAR_REAL_SWRT_DTL_TO_HDHS_c_01(table):
        process_in_batches(table['table'], table['columns'])
    @task(task_id="task_RAR_REAL_SWRT_ETC_DTL_TO_HDHS_c_01", trigger_rule="all_done")
    def task_RAR_REAL_SWRT_ETC_DTL_HDHS_c_01(table):
        process_in_batches(table['table'], table['columns'])

    @task(task_id="task_RAR_REAL_SWRT_ONLN_DTL_TO_HDHS_c_01", trigger_rule="all_done")
    def task_RAR_REAL_SWRT_ONLN_DTL_TO_HDHS_c_01(table):
        process_in_batches(table['table'], table['columns'])

    @task(task_id="task_RAR_REAL_SWRT_ONLN_ETC_DTL_TO_HDHS_c_01", trigger_rule="all_done")
    def task_RAR_REAL_SWRT_ONLN_ETC_DTL_TO_HDHS_c_01(table):
        process_in_batches(table['table'], table['columns'])


    task_RAR_REAL_SWRT_DTL_TO_HDHS_c_01(TABLE_NAME_LIST[0]) >> \
    task_RAR_REAL_SWRT_ETC_DTL_HDHS_c_01(TABLE_NAME_LIST[1]) >> \
    task_RAR_REAL_SWRT_ONLN_DTL_TO_HDHS_c_01(TABLE_NAME_LIST[2]) >> \
    task_RAR_REAL_SWRT_ONLN_ETC_DTL_TO_HDHS_c_01(TABLE_NAME_LIST[3])






