
# v26

from airflow.decorators import dag
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.models.baseoperator import chain
from jwcrypto import jwk
import json
from pendulum import datetime

def get_pubkey_f(**kwargs):
    """Convert k8s cluster jwk pub key to pem format and print/return"""
    ti = kwargs['ti']
    jwk_json = ti.xcom_pull(task_ids="k_get_signing_key")
    jwk_obj = json.loads(jwk_json)
    
    key0 = jwk_obj['keys'][0]

    key = jwk.JWK(**key0)
    pubpem = key.export_to_pem().decode("utf-8")[:-1]

    # print('''\nVAULT CONFIG CMD:\nvault write auth/jwt/config jwt_validation_pubkeys="%s" \n\n''' % pubpem)
    return pubpem

def print_vault_cmds_f(**kwargs):
    ti = kwargs['ti']
    xcom_pubkey = ti.xcom_pull(task_ids="get_pubkey")
    xcom_audience = ti.xcom_pull(task_ids="get_jwt_audience")
    xcom_subject = ti.xcom_pull(task_ids="get_jwt_subject")

    vault_cmds = f""" 
\n# BEGIN VAULT SERVER CONFIG
vault auth enable jwt
\nvault write auth/jwt/config jwt_validation_pubkeys="{xcom_pubkey}"
\nvault write auth/jwt/role/my-role \\
   role_type="jwt" \\
   bound_audiences="{xcom_audience}" \\
   user_claim="sub" \\
   bound_subject="{xcom_subject}" \\
   policies="default,db-policy" \\
   ttl="1h"    

# END VAULT CONFIG

# login command
vault write auth/jwt/login role=my-role jwt=@token
\n\n\n
"""
    print(vault_cmds)


@dag(start_date=datetime(2022, 8, 1), schedule=None, catchup=False)
def vault_jwt_auth_setup():

    k_get_jwks_uri = BashOperator(
        task_id="k_get_jwks_uri",
        bash_command='kubectl get --raw /.well-known/openid-configuration | jq -r ".jwks_uri"',
    )

    k_get_signing_key = BashOperator(
        task_id="k_get_signing_key",
        bash_command="kubectl get --raw {{ ti.xcom_pull(task_ids='k_get_jwks_uri') }} ",
    )

    get_pubkey = PythonOperator(
        task_id="get_pubkey",
        python_callable=get_pubkey_f,
        provide_context=True,
    )

    print_vault_cmds = PythonOperator(
        task_id="print_vault_cmds",
        python_callable=print_vault_cmds_f,
        provide_context=True,
    )

    print_jwt_raw = BashOperator(
        task_id="print_jwt_raw",
        bash_command="cat /var/run/secrets/kubernetes.io/serviceaccount/token",
    )

    get_jwt_audience = BashOperator(
        task_id="get_jwt_audience",
        bash_command="cat /var/run/secrets/kubernetes.io/serviceaccount/token | step crypto jwt inspect --insecure  | jq -r '.payload.aud[0]'",
    )

    get_jwt_subject = BashOperator(
        task_id="get_jwt_subject",
        bash_command="cat /var/run/secrets/kubernetes.io/serviceaccount/token | step crypto jwt inspect --insecure  | jq -r '.payload.sub'",
    )

    get_jwt_issuer = BashOperator(
        task_id="get_jwt_issuer",
        bash_command="cat /var/run/secrets/kubernetes.io/serviceaccount/token | step crypto jwt inspect --insecure  | jq -r '.payload.iss'",
    )

    verify_jwt = BashOperator(
        task_id="verify_jwt",
        bash_command="echo '{{ ti.xcom_pull(task_ids=\'get_pubkey\') }}' > /tmp/pub.key && cat /var/run/secrets/kubernetes.io/serviceaccount/token | step crypto jwt verify --key /tmp/pub.key --iss '{{ ti.xcom_pull(task_ids=\'get_jwt_issuer\') }}' --aud '{{ ti.xcom_pull(task_ids=\'get_jwt_audience\') }}' --alg RS256",
    )

    chain(
        k_get_jwks_uri,
        k_get_signing_key,
        get_pubkey,
    )
    get_pubkey >> print_vault_cmds
    get_jwt_audience >> print_vault_cmds
    get_jwt_subject >> print_vault_cmds
    get_jwt_issuer >> print_vault_cmds
    print_vault_cmds >> verify_jwt

vault_jwt_auth_setup()