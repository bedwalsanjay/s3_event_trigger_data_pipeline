import os
import re
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

GLUE_JOB_NAME = os.environ["GLUE_JOB_NAME"]
EXPECTED_PREFIX = "source_files/orders/"
FILE_PATTERN = re.compile(r"^part-\d{5}_orders_\d+\.csv$")

glue = boto3.client("glue")


def lambda_handler(event, context):
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        logger.info("Received s3://%s/%s", bucket, key)

        if not key.startswith(EXPECTED_PREFIX):
            logger.warning("Unexpected prefix, skipping: %s", key)
            continue

        filename = key.split("/")[-1]

        if not FILE_PATTERN.match(filename):
            logger.error("Invalid file name: %s", filename)
            continue

        logger.info("Valid file: %s — triggering Glue job '%s'", filename, GLUE_JOB_NAME)

        response = glue.start_job_run(
            JobName=GLUE_JOB_NAME,
            Arguments={
                "--source_bucket": bucket,
                "--source_key": key,
            },
        )
        logger.info("Glue job run started: %s", response["JobRunId"])
