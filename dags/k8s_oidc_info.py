
# v7

from airflow.decorators import dag
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.models.baseoperator import chain


from pendulum import datetime

def print_pubkey(**kwargs):
    """Convert k8s cluster jwk pub key to pem format and print/return"""
    ti = kwargs['ti']
    jwk_json = ti.xcom_pull(task_ids="k_get_signing_key")
    print(jwk_json)
    return jwk_json 

@dag(start_date=datetime(2022, 8, 1), schedule=None, catchup=False)
def k8s_oidc_info():

    # k_get_oidc_config = BashOperator(
    #     task_id="k_get_oidc_config",
    #     bash_command='kubectl get --raw /.well-known/openid-configuration',
    # )

    k_get_jwks_uri = BashOperator(
        task_id="k_get_jwks_uri",
        bash_command='kubectl get --raw /.well-known/openid-configuration | jq -r ".jwks_uri"',
    )

    k_get_signing_key = BashOperator(
        task_id="k_get_signing_key",
        bash_command="kubectl get --raw {{ ti.xcom_pull(task_ids='k_get_jwks_uri') }} ",
    )

    print_pubkey_task = PythonOperator(
        task_id="print_pubkey",
        python_callable=print_pubkey,
        provide_context=True,
    )

    # run_this = print_pubkey()

    # curl_oidc_config = BashOperator(
    #     task_id="curl_oidc_config",
    #     bash_command="curl -k -H \"Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)\" https://kubernetes.default.svc/.well-known/openid-configuration",
    # )

    print_jwt = BashOperator(
        task_id="print_jwt",
        bash_command="cat /var/run/secrets/kubernetes.io/serviceaccount/token",
    )

    # get_keys = BashOperator(
    #     task_id="get_keys",
    #     bash_command="echo {{ ti.xcom_pull(task_ids='retrieve_oidc') }}"
    # )

    # install_kubectl >> run_kubectl >> retrieve_oidc >> get_keys
    # run_kubectl >> retrieve_oidc >> get_keys

    chain(
        k_get_jwks_uri,
        k_get_signing_key,
        print_pubkey_task,
    )
    print_jwt

k8s_oidc_info()