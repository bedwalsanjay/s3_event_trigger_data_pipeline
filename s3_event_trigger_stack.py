from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration,
)
from constructs import Construct


class S3EventTriggerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # CDK-owned bucket
        bucket = s3.Bucket(self, "SourceBucket", bucket_name="roh-source-2026")

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
            resources=[f"arn:aws:glue:{self.region}:{self.account}:job/job1"],
        ))

        # Lambda function
        lambda_fn = _lambda.Function(self, "ValidateAndTrigger",
            function_name="roh-validate-and-trigger",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="validate_and_trigger.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            role=lambda_role,
            timeout=Duration.seconds(30),
        )

        # S3 event notification — only for source_files/orders/ prefix, .csv suffix
        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(lambda_fn),
            s3.NotificationKeyFilter(
                prefix="source_files/orders/",
                suffix=".csv",
            ),
        )
