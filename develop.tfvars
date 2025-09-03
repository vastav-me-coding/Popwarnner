environment = "develop"
account_id = "968921834094"
private_subnet_0_name = "AWS-AFFINITY-US-DEVI1-VDC-PrivateSubnet0"
security_group_web_name = "DEVINT-AON-WEB-ACCESS"
security_group_app_common_name = "DEVINT-COMMON-APP-ACCESS"
security_group_db_common_name = "DEVINT-COMMON-DB-ACCESS"
security_group_db_name = "DEVINT-AON-DB-ACCESS"
vpc_id = "vpc-0ced58fcc9c685c28"
region = "us-east-1"
appid = "AR4262-DV001"

kms_key_id="a7e9e213-4086-48cf-af1e-918e65c5f390"
lambda_name = "tds-sqs-pw-submission"
image_uri = ""
lambda_execution_role_name = "affinity-tds-ar4262-dv001-sqs-lambda-role"
lambda_execution_role_arn = "arn:aws:iam::968921834094:role/app/affinity-tds-ar4262-dv001-sqs-lambda-role"
rds_credentials_secret_arn = "arn:aws:secretsmanager:us-east-1:968921834094:secret:affinity-ods2-ar4262-dv001-rds-master-credentials-169S6S"
rds_cluster_endpoint = "affinity-ods2-develop.cluster-cj3qp6qspcpk.us-east-1.rds.amazonaws.com"
aumine_credentials_secret_arn = "arn:aws:secretsmanager:us-east-1:968921834094:secret:affinity-tds-ar4262-dv001-audbm-aumods-credentials-secret-tOkXG3"

deployments = {
     ods_aws_lambda_apis_multiple = {
        "r112" = {
            enabled = true
            overrides = {
                appid = "AR4262-DV001"
            }
        }
    }
}