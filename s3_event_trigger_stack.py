from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_s3_assets as s3_assets,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_glue as glue,
    Duration,
    RemovalPolicy,
)
from constructs import Construct
from config import GLUE_JOB_NAME, SOURCE_BUCKET, TARGET_BUCKET


class S3EventTriggerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Source bucket
        source_bucket = s3.Bucket(self, "SourceBucket",
            bucket_name=SOURCE_BUCKET,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Target bucket
        target_bucket = s3.Bucket(self, "TargetBucket",
            bucket_name=TARGET_BUCKET,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # IAM role for Glue job
        glue_role = iam.Role(self, "GlueRole",
            role_name="roh-glue-orders-role",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole"),
            ],
        )
        source_bucket.grant_read(glue_role)
        target_bucket.grant_write(glue_role)

        # Upload Glue script as CDK asset
        glue_script = s3_assets.Asset(self, "GlueScript", path="glue/orders_job.py")
        glue_script.grant_read(glue_role)

        # Glue job (script uploaded to source bucket under glue/ prefix)
        glue_job = glue.CfnJob(self, "OrdersGlueJob",
            name=GLUE_JOB_NAME,
            role=glue_role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="pythonshell",
                python_version="3.9",
                script_location=glue_script.s3_object_url,
            ),
            default_arguments={
                "--target_bucket": TARGET_BUCKET,
                "--extra-py-files": "",
            },
            glue_version="3.0",
            max_capacity=0.0625,  # 1 DPU for pythonshell
        )

        # IAM role for Lambda
        lambda_role = iam.Role(self, "LambdaRole",
            role_name="roh-validate-trigger-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ],
        )
        lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["glue:StartJobRun"],
            resources=[f"arn:aws:glue:{self.region}:{self.account}:job/{GLUE_JOB_NAME}"],
        ))

        # Lambda function
        lambda_fn = _lambda.Function(self, "ValidateAndTrigger",
            function_name="roh-validate-and-trigger",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="validate_and_trigger.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            role=lambda_role,
            timeout=Duration.seconds(30),
            environment={"GLUE_JOB_NAME": GLUE_JOB_NAME},
        )

        # S3 event notification
        source_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(lambda_fn),
            s3.NotificationKeyFilter(prefix="source_files/orders/", suffix=".csv"),
        )
