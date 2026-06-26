import re
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

GLUE_JOB_NAME = "job1"
EXPECTED_PREFIX = "source_files/orders/"
# Matches: part-NNNNN_orders_N.csv  (N = one or more digits)
FILE_PATTERN = re.compile(r"^part-\d{5}_orders_\d+\.csv$")

glue = boto3.client("glue")


def lambda_handler(event, context):
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        logger.info("Received s3://%s/%s", bucket, key)

        # Validate path prefix
        if not key.startswith(EXPECTED_PREFIX):
            logger.warning("Unexpected prefix, skipping: %s", key)
            continue

        filename = key.split("/")[-1]

        # Validate file name convention
        if not FILE_PATTERN.match(filename):
            logger.error("Invalid file name: %s — does not match pattern part-NNNNN_orders_N.csv", filename)
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
