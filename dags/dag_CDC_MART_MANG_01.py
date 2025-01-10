from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
import pendulum
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

# Define the task function
def execute_procedure(procedure_name, p_start, p_end):
    snowflake_hook = SnowflakeHook(snowflake_conn_id='conn_snowflake_etl')

    with snowflake_hook.get_conn() as conn:
        with conn.cursor() as cur:
            query = f"CALL ETL_SERVICE.{procedure_name}({p_start}, {p_end})"
            print(query)

def log_etl_completion(**kwargs):
    complete_time = kwargs['execution_date'].in_tz(pendulum.timezone("Asia/Seoul")).strftime('%Y-%m-%d %H:%M:%S')
    print(f"*** {complete_time} : CDC_MART_LEV_02 프로시져 실행 완료 **")

with DAG(
    dag_id="dag_CDC_MART_MANG_01",
    schedule_interval=None,
    tags=["현대홈쇼핑","MART프로시져"]
) as dag:
    task_SP_RAR_BMNG_ARLT_DLU_FCT = PythonOperator(
        task_id="task_SP_RAR_BMNG_ARLT_DLU_FCT",
        python_callable=execute_procedure,
        op_args=["SP_RAR_BMNG_ARLT_DLU_FCT", p_start, p_end],
        trigger_rule="all_done"
    )

    task_SP_BOD_RNTL_ORD_DTL = PythonOperator(
        task_id="task_SP_BOD_RNTL_ORD_DTL",
        python_callable=execute_procedure,
        op_args=["SP_BOD_RNTL_ORD_DTL", p_start, p_end],
        trigger_rule="all_done"
    )

    task_SP_RAR_BMNG_ARLT_DLU_SMR = PythonOperator(
        task_id="task_SP_RAR_BMNG_ARLT_DLU_SMR",
        python_callable=execute_procedure,
        op_args=["SP_RAR_BMNG_ARLT_DLU_SMR", p_start, p_end],
        trigger_rule="all_done"
    )

    task_SP_RAR_HMALL_BMNG_ARLT_DLU_SMR = PythonOperator(
        task_id="task_SP_RAR_HMALL_BMNG_ARLT_DLU_SMR",
        python_callable=execute_procedure,
        op_args=["SP_RAR_HMALL_BMNG_ARLT_DLU_SMR", p_start, p_end],
        trigger_rule="all_done"
    )

    task_SP_RAR_HS_BMNG_ARLT_DLU_SMR = PythonOperator(
        task_id="task_SP_RAR_HS_BMNG_ARLT_DLU_SMR",
        python_callable=execute_procedure,
        op_args=["SP_RAR_HS_BMNG_ARLT_DLU_SMR", p_start, p_end],
        trigger_rule="all_done"
    )

    task_SP_RAR_SRCN_MD_ARLT_DLU_SMR = PythonOperator(
        task_id="task_SP_RAR_SRCN_MD_ARLT_DLU_SMR",
        python_callable=execute_procedure,
        op_args=["SP_RAR_SRCN_MD_ARLT_DLU_SMR", p_start, p_end],
        trigger_rule="all_done"
    )

    task_SP_RAR_BMNG_ARLT_DLU_ACPT_META_FCT = PythonOperator(
        task_id="task_SP_RAR_BMNG_ARLT_DLU_ACPT_META_FCT",
        python_callable=execute_procedure,
        op_args=["SP_RAR_BMNG_ARLT_DLU_ACPT_META_FCT", p_start, p_end],
        trigger_rule="all_done"
    )

    task_SP_RAR_BMNG_ARLT_DLU_ACPT_META_FCT_02 = PythonOperator(
        task_id="task_SP_RAR_BMNG_ARLT_DLU_ACPT_META_FCT_02",
        python_callable=execute_procedure,
        op_args=["SP_RAR_BMNG_ARLT_DLU_ACPT_META_FCT_02", p_start, p_end],
        trigger_rule="all_done"
    )

    task_SP_POD_ACPT_META_ORD_ANAL_DLU_FCT_01 = PythonOperator(
        task_id="task_SP_POD_ACPT_META_ORD_ANAL_DLU_FCT_01",
        python_callable=execute_procedure,
        op_args=["SP_POD_ACPT_META_ORD_ANAL_DLU_FCT_01", p_start, p_end],
        trigger_rule="all_done"
    )

    task_SP_POD_ACPT_META_ORD_ANAL_DLU_FCT_02 = PythonOperator(
        task_id="task_SP_POD_ACPT_META_ORD_ANAL_DLU_FCT_02",
        python_callable=execute_procedure,
        op_args=["SP_POD_ACPT_META_ORD_ANAL_DLU_FCT_02", p_start, p_end],
        trigger_rule="all_done"
    )

    task_SP_POD_ACPT_META_ORD_ANAL_DLU_FCT_03 = PythonOperator(
        task_id="task_SP_POD_ACPT_META_ORD_ANAL_DLU_FCT_03",
        python_callable=execute_procedure,
        op_args=["SP_POD_ACPT_META_ORD_ANAL_DLU_FCT_03", p_start, p_end],
        trigger_rule="all_done"
    )

    task_ETL_DAILY_LOG = PythonOperator(
        task_id="task_ETL_DAILY_LOG",
        python_callable=log_etl_completion,
        provide_context=True,
        trigger_rule="all_done"
    )

    task_SP_RAR_BMNG_ARLT_DLU_FCT >> [task_SP_BOD_RNTL_ORD_DTL, task_SP_RAR_BMNG_ARLT_DLU_SMR]

    task_SP_RAR_BMNG_ARLT_DLU_SMR >> task_SP_RAR_HMALL_BMNG_ARLT_DLU_SMR >> task_SP_RAR_HS_BMNG_ARLT_DLU_SMR >> task_SP_RAR_SRCN_MD_ARLT_DLU_SMR >> task_SP_RAR_BMNG_ARLT_DLU_ACPT_META_FCT >> task_SP_RAR_BMNG_ARLT_DLU_ACPT_META_FCT_02 >> task_SP_POD_ACPT_META_ORD_ANAL_DLU_FCT_01 >> task_SP_POD_ACPT_META_ORD_ANAL_DLU_FCT_02 >> task_SP_POD_ACPT_META_ORD_ANAL_DLU_FCT_03

    [task_SP_BOD_RNTL_ORD_DTL, task_SP_POD_ACPT_META_ORD_ANAL_DLU_FCT_03] >> task_ETL_DAILY_LOG


