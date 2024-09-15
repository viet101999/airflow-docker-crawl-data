from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import shutil
import os

# Define default args for the DAG
default_args = {
    'owner': 'vietdh',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
with DAG(
    'git_clone_and_run_dag',
    default_args=default_args,
    description='DAG to clone code from GitHub and run it',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    # Task 1: Clone code from GitHub repository
    git_clone_task = BashOperator(
        task_id='git_clone_code',
        bash_command='rm -rf MiAI_Airflow && git clone https://github.com/thangnch/MiAI_Airflow.git MiAI_Airflow',
    )

    # Task 2: Move the cloned code to the DAGs folder
    def move_to_dags():
        src_path = "MiAI_Airflow/simple_dag_local.py"
        dest_path = "/opt/airflow/dags"

        # Check if source path exists
        # if os.path.exists(src_path):
        #     # Copy all files and directories from the source to the destination
        #     for item in os.listdir(src_path):
        #         s = os.path.join(src_path, item)
        #         d = os.path.join(dest_path, item)
        #         if os.path.isdir(s):
        #             shutil.copytree(s, d, dirs_exist_ok=True)
        #         else:
        #             shutil.copy2(s, d)
        if os.path.exists(src_path):
            shutil.copy2(src_path, dest_path)

    move_code_task = PythonOperator(
        task_id='move_code_to_dags',
        python_callable=move_to_dags,
    )

    # Task 3: Trigger a DAG run (if required)
    trigger_dag_run_task = BashOperator(
        task_id='trigger_dag_run',
        bash_command='airflow dags trigger thangnc_dag01a',
    )

    # Task pipeline
    git_clone_task >> move_code_task >> trigger_dag_run_task
