from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from common.common_call_procedure import execute_procedure, execute_procedure_dycl, log_etl_completion
from datetime import datetime, timedelta
import boto3
import json

# S3 parameters
s3 = boto3.client('s3')
bucket_name = "hdhs-dw-mwaa-s3"
key = "param/wf_DD01_0030_DAILY_MAIN_01.json"
response = s3.get_object(Bucket=bucket_name, Key=key)
params = json.load(response['Body'])

p_start = params.get("$$P_START")
p_end = params.get("$$P_END")


with DAG(
    dag_id="dag_CDC_MART_LEV_03",
    schedule_interval=None,
    tags=["현대홈쇼핑","dag_CDC_MART_01","MART프로시져"]
) as dag:
    task_SP_RCA_THDY_TMR_FCT = PythonOperator(
        task_id="task_SP_RCA_THDY_TMR_FCT",
        python_callable=execute_procedure,
        op_args=["SP_RCA_THDY_TMR_FCT", p_start, p_end, 'conn_snowflake_etl'],
        trigger_rule="all_done"
    )

    task_SP_RMA_BROD_COPN_PBLC_DTL = PythonOperator(
        task_id="task_SP_RMA_BROD_COPN_PBLC_DTL",
        python_callable=execute_procedure,
        op_args=["SP_RMA_BROD_COPN_PBLC_DTL", p_start, p_end, 'conn_snowflake_etl'],
        trigger_rule="all_done"
    )

    task_SP_BCU_HMALL_CUST_MST = PythonOperator(
        task_id="task_SP_BCU_HMALL_CUST_MST",
        python_callable=execute_procedure,
        op_args=["SP_BCU_HMALL_CUST_MST", p_start, p_end, 'conn_snowflake_etl'],
        trigger_rule="all_done"
    )

    task_SP_RDM_HMALL_SECT_DPTH_DIM = PythonOperator(
        task_id="task_SP_RDM_HMALL_SECT_DPTH_DIM",
        python_callable=execute_procedure,
        op_args=["SP_RDM_HMALL_SECT_DPTH_DIM", p_start, p_end, 'conn_snowflake_etl'],
        trigger_rule="all_done"
    )

    task_SP_RMA_HMALL_COPN_PBLC_DTL = PythonOperator(
        task_id="task_SP_RMA_HMALL_COPN_PBLC_DTL",
        python_callable=execute_procedure,
        op_args=["SP_RMA_HMALL_COPN_PBLC_DTL", p_start, p_end, 'conn_snowflake_etl'],
        trigger_rule="all_done"
    )

    task_SP_ROD_SO_OPER_MOTH_SMR = PythonOperator(
        task_id="task_SP_ROD_SO_OPER_MOTH_SMR",
        python_callable=execute_procedure,
        op_args=["SP_ROD_SO_OPER_MOTH_SMR", p_start, p_end, 'conn_snowflake_etl'],
        trigger_rule="all_done"
    )

    task_ETL_DAILY_LOG = PythonOperator(
        task_id="task_ETL_DAILY_LOG",
        python_callable=log_etl_completion,
        provide_context=True,
        trigger_rule="all_done"
    )

    [task_SP_BCU_HMALL_CUST_MST,task_SP_RMA_BROD_COPN_PBLC_DTL,task_SP_RCA_THDY_TMR_FCT]

    task_SP_BCU_HMALL_CUST_MST >> task_SP_RDM_HMALL_SECT_DPTH_DIM

    task_SP_RMA_BROD_COPN_PBLC_DTL >> task_SP_RMA_HMALL_COPN_PBLC_DTL >> task_SP_ROD_SO_OPER_MOTH_SMR

    [task_SP_RCA_THDY_TMR_FCT, task_SP_RDM_HMALL_SECT_DPTH_DIM, task_SP_ROD_SO_OPER_MOTH_SMR] >> task_ETL_DAILY_LOG
