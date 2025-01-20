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


def log_result_to_snowflake(procedure_name, start_time, end_time, result, p_start, p_end):
    """
    Logs the result of a procedure execution to Snowflake table.
    """
    snowflake_hook = SnowflakeHook(snowflake_conn_id='conn_snowflake_etl')
    # Ensure result is not None
    result = result or "No result returned"

    # Check for errors in result
    if 'SQL compilation error' in result or 'Procedure execute error' in result:
        status = 'ER'
    else:
        status = 'OK'

    message = result.replace("'", "''")
    jb_pmt = f'[{p_start}]-[{p_end}]'

    query = f"""
    INSERT INTO DW_ETL_DB.CONFIG.JOB_RESULT (
        PGMID, STARTTIME, ENDTIME, ST, JBPMT, MSG
    )
    VALUES (
        '{procedure_name}', '{start_time}', '{end_time}', '{status}', '{jb_pmt}', '{message}'
    )
    """
    print(query)

    with snowflake_hook.get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query)


def execute_procedure(procedure_name, p_start, p_end):
    """
    Executes a stored procedure in Snowflake and logs the result.
    """
    snowflake_hook = SnowflakeHook(snowflake_conn_id='conn_snowflake_etl')
    start_time = pendulum.now("Asia/Seoul")

    try:
        with snowflake_hook.get_conn() as conn:
            with conn.cursor() as cur:
                query = f"CALL ETL_SERVICE.{procedure_name}('{p_start}', '{p_end}')"
                print(query)
                cur.execute(query)
                result = cur.fetchall()
                # Handle empty result properly
                result_message = result[0][0] if result and result[0] else "No result returned"
                print(f"Procedure result: {result_message}")
    except Exception as e:
        result_message = str(e)
        print(f"Procedure execute error message: {result_message}")
    end_time = pendulum.now("Asia/Seoul")

    # Log the result to Snowflake
    log_result_to_snowflake(procedure_name, start_time, end_time, result_message, p_start, p_end)


def log_etl_completion(**kwargs):
    complete_time = kwargs['execution_date'].in_tz(pendulum.timezone("Asia/Seoul")).strftime('%Y-%m-%d %H:%M:%S')
    print(f"*** {complete_time} : CDC_MART_LEV_02 프로시져 실행 완료 **")

# Define the DAG
with DAG(
    dag_id="dag_CDC_MART_VLID_TERM_01",
    schedule_interval=None,
    tags=["현대홈쇼핑","MART프로시져"]
) as dag:
    task_SP_BCU_CUST_STAT_MST = PythonOperator(
        task_id="task_SP_BCU_CUST_STAT_MST",
        python_callable=execute_procedure,
        op_args=["SP_BCU_CUST_STAT_MST", p_start, p_end],
        trigger_rule="all_done"
    )

    task_SP_BMK_CUST_VLID_TERM_EMAIL_DTL = PythonOperator(
        task_id="task_SP_BMK_CUST_VLID_TERM_EMAIL_DTL",
        python_callable=execute_procedure,
        op_args=["SP_BMK_CUST_VLID_TERM_EMAIL_DTL", p_start, p_end],
        trigger_rule="all_done"
    )

    task_SP_DWCU_CUST_SMS_DROPT = PythonOperator(
        task_id="task_SP_DWCU_CUST_SMS_DROPT",
        python_callable=execute_procedure,
        op_args=["SP_DWCU_CUST_SMS_DROP", p_start, p_end],
        trigger_rule="all_done"
    )

    task_SP_DWCU_CUST_INSU_DROP = PythonOperator(
        task_id="task_SP_DWCU_CUST_INSU_DROP",
        python_callable=execute_procedure,
        op_args=["SP_DWCU_CUST_INSU_DROP", p_start, p_end],
        trigger_rule="all_done"
    )

    task_SP_BCU_CUST_STAT_MST >> \
    task_SP_BMK_CUST_VLID_TERM_EMAIL_DTL >> \
    task_SP_DWCU_CUST_SMS_DROPT >> \
    task_SP_DWCU_CUST_INSU_DROP





