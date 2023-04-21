from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import hvac
from airflow.models.connection import Connection
import subprocess
import os


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

def get_vault_token():
    
    # get Vault role and auth method path (relative to VAULT_NAMESPACE, if set in env)
    vault_role = os.getenv('VAULT_ROLE')
    vault_auth_path = os.getenv('VAULT_AUTH_PATH')

    # read JWT from pod filesystem
    with open('/var/run/secrets/kubernetes.io/serviceaccount/token', mode='r') as f:
        token = f.readline()
    
    # Instantiate a HashiCorp Vault client
    # This expects VAULT_ADDR (and VAULT_NAMESPACE, if needed) in the environment
    vault_client = hvac.Client()

    response = vault_client.auth.jwt.jwt_login(role=vault_role, jwt=token, use_token=True, path=vault_auth_path)
    print('Client token returned: %s' % response['auth']['client_token'])

    # cmd_str = f"""airflow connections add 'my_prod_db' \
    #                 --conn-type 'mysql' \
    #                 --conn-login '{user}' \
    #                 --conn-password '{passwd}' \
    #                 --conn-host '{hostname}' \
    #                 --conn-port '{port}' """

    # print(cmd_str)
    # subprocess.run(cmd_str, shell=True)

    return response['auth']['client_token']

def retrieve_and_store_db_credentials():
    # Instantiate a HashiCorp Vault client
    # This expects VAULT_TOKEN and VAULT_ADDR in the environment
    vault_client = hvac.Client()
    
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
