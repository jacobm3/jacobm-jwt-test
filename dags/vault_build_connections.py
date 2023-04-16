from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from hvac import Client
from airflow.models.connection import Connection
import subprocess


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 4, 15),
    'schedule': '@hourly',
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'retrieve_db_credentials',
    default_args=default_args,
    description='Retrieve dynamic mysql credentials from HashiCorp Vault and store them as an Airflow connection',
    schedule_interval=timedelta(days=1)
)

def retrieve_and_store_db_credentials():
    # Instantiate a HashiCorp Vault client
    # This expects VAULT_TOKEN and VAULT_ADDR in the environment
    vault_client = Client()
    
    # Read the database credentials from Vault
    db_creds = vault_client.secrets.database.generate_credentials(mount_point='database', name='db1-5s')
    user = db_creds['data']['username']
    passwd = db_creds['data']['password']
    hostname = 'mysql-dev'
    port = 3306

    cmd_str = f"""airflow connections add 'my_prod_db' \
                    --conn-type 'mysql' \
                    --conn-login '{user}' \
                    --conn-password '{passwd}' \
                    --conn-host '{hostname}' \
                    --conn-port '{port}' """

    print(cmd_str)
    subprocess.run(cmd_str, shell=True)


with dag:
    retrieve_db_credentials_task = PythonOperator(
        task_id='retrieve_db_credentials',
        python_callable=retrieve_and_store_db_credentials
    )
    
    retrieve_db_credentials_task
