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
        bash_command='rm -rf /opt/airflow/git_repo/vietdh_airflow && git clone https://github.com/viet101999/airflow-docker-crawl-data.git /opt/airflow/git_repo/vietdh_airflow',
    )

    # Task 2: Move the cloned code to the DAGs folder
    def move_to_dags():
        src_path = "/opt/airflow/git_repo/vietdh_airflow/dags/crawl_data.py"
        dest_path = "/opt/airflow/dags"

        # Ensure the DAGs folder exists
        if os.path.exists(src_path):
            shutil.copy2(src_path, dest_path)
            print(f"Moved {src_path} to {dest_path}")
        else:
            print(f"Source path {src_path} does not exist")

    move_code_task = PythonOperator(
        task_id='move_code_to_dags',
        python_callable=move_to_dags,
    )

    # Task 3: Trigger the newly moved DAG
    trigger_dag_run_task = BashOperator(
        task_id='trigger_new_crawl_dag',
        bash_command='airflow dags trigger crawl_data',
    )

    # Task pipeline
    git_clone_task >> move_code_task >> trigger_dag_run_task
