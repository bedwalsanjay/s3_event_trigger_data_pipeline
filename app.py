#!/usr/bin/env python3
import aws_cdk as cdk
from s3_event_trigger_stack import S3EventTriggerStack

app = cdk.App()
S3EventTriggerStack(app, "S3EventTriggerStack",
    env=cdk.Environment(region="ap-south-1"),
)
app.synth()
