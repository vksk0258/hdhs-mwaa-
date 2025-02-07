from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from operators.etl_schedule_update_operator import etlScheduleUpdateOperator
from datetime import timedelta
import pendulum


with DAG(
    dag_id="dag_DD01_0630_DAILY_BROAD_01",
    schedule_interval='30 6 * * *',
    start_date=pendulum.datetime(2025, 2, 5, tz="Asia/Seoul"),
    dagrun_timeout=timedelta(minutes=4000),
    tags=["현대홈쇼핑","100_COM"]
) as dag:
    task_ETL_SCHEDULE_c_01 = etlScheduleUpdateOperator(
        task_id="task_ETL_SCHEDULE_c_01"
    )

    trigger_dag_CDC_MART_DAILY_ARLT_01 = TriggerDagRunOperator(
        task_id='trigger_dag_CDC_MART_DAILY_ARLT_01',
        trigger_dag_id='dag_CDC_MART_DAILY_ARLT_01',
        reset_dag_run=True,  # 이미 수행된 dag여도 수행 할 것인지
        wait_for_completion=True,  # 트리거 하는 dag가 끝날때까지 기다릴 것인지
        poke_interval=60,
        allowed_states=['success'],  # 트리거 하는 dag가 어떤 상태여야 오퍼레이터가 성공으로 끝나는지
        trigger_rule="all_done"
    )

    trigger_dag_CDC_MART_DAILY_BROAD_01 = TriggerDagRunOperator(
        task_id='trigger_dag_CDC_MART_DAILY_BROAD_01',
        trigger_dag_id='dag_CDC_MART_DAILY_BROAD_01',
        reset_dag_run=True,  # 이미 수행된 dag여도 수행 할 것인지
        wait_for_completion=True,  # 트리거 하는 dag가 끝날때까지 기다릴 것인지
        poke_interval=60,
        allowed_states=['success'],  # 트리거 하는 dag가 어떤 상태여야 오퍼레이터가 성공으로 끝나는지
        trigger_rule="all_done"
    )

    trigger_dag_CDC_MART_DAILY_DRCT_DASH_BOARD_01 = TriggerDagRunOperator(
        task_id='trigger_dag_CDC_MART_DAILY_DRCT_DASH_BOARD_01',
        trigger_dag_id='dag_CDC_MART_DAILY_DRCT_DASH_BOARD_01',
        reset_dag_run=True,  # 이미 수행된 dag여도 수행 할 것인지
        wait_for_completion=True,  # 트리거 하는 dag가 끝날때까지 기다릴 것인지
        poke_interval=60,
        allowed_states=['success'],  # 트리거 하는 dag가 어떤 상태여야 오퍼레이터가 성공으로 끝나는지
        trigger_rule="all_done"
    )

    # 역방향
    # trigger_dag_CDC_ODS_DAILY_ARLT_TO_HDHS_01 = TriggerDagRunOperator(
    #     task_id='trigger_dag_CDC_ODS_DAILY_ARLT_TO_HDHS_01',
    #     trigger_dag_id='dag_CDC_ODS_DAILY_ARLT_TO_HDHS_01',
    #     reset_dag_run=True,  # 이미 수행된 dag여도 수행 할 것인지
    #     wait_for_completion=True,  # 트리거 하는 dag가 끝날때까지 기다릴 것인지
    #     poke_interval=60,
    #     allowed_states=['success'],  # 트리거 하는 dag가 어떤 상태여야 오퍼레이터가 성공으로 끝나는지
    #     trigger_rule="all_done"
    # )

    trigger_dag_CDC_MART_DAILY_PGM_FCT_01 = TriggerDagRunOperator(
        task_id='trigger_dag_CDC_MART_DAILY_PGM_FCT_01',
        trigger_dag_id='dag_CDC_MART_DAILY_PGM_FCT_01',
        reset_dag_run=True,  # 이미 수행된 dag여도 수행 할 것인지
        wait_for_completion=True,  # 트리거 하는 dag가 끝날때까지 기다릴 것인지
        poke_interval=60,
        allowed_states=['success'],  # 트리거 하는 dag가 어떤 상태여야 오퍼레이터가 성공으로 끝나는지
        trigger_rule="all_done"
    )

    # task_ETL_SCHEDULE_c_01 >> [trigger_dag_CDC_MART_DAILY_ARLT_01,trigger_dag_CDC_MART_DAILY_BRAOD_01]
    #
    # trigger_dag_CDC_MART_DAILY_BRAOD_01 >> trigger_dag_CDC_MART_DAILY_DRCT_DASH_BROAD_01
    #
    # trigger_dag_CDC_MART_DAILY_ARLT_01 >> trigger_dag_CDC_ODS_DAILY_ARLT_TO_HDHS_01
    #
    # [trigger_dag_CDC_MART_DAILY_DRCT_DASH_BROAD_01, trigger_dag_CDC_ODS_DAILY_ARLT_TO_HDHS_01] >> \
    # trigger_dag_CDC_MART_DAILY_PGM_FCT_01

    task_ETL_SCHEDULE_c_01 >> [trigger_dag_CDC_MART_DAILY_ARLT_01,trigger_dag_CDC_MART_DAILY_BROAD_01]

    trigger_dag_CDC_MART_DAILY_BROAD_01 >> trigger_dag_CDC_MART_DAILY_DRCT_DASH_BOARD_01

    [trigger_dag_CDC_MART_DAILY_DRCT_DASH_BOARD_01, trigger_dag_CDC_MART_DAILY_ARLT_01] >> \
    trigger_dag_CDC_MART_DAILY_PGM_FCT_01
