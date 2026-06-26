# S3 Event Trigger Data Pipeline

Deploys a Lambda function that fires on S3 object uploads to `edp-source-26/source_files/orders/*.csv` and starts Glue job `job1`.

## Setup

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Bootstrap (first time only per account/region)
cdk bootstrap aws://ACCOUNT_ID/ap-south-1

# Deploy
cdk deploy
```

## Architecture

```
S3 (edp-source-26)
  └─ ObjectCreated (source_files/orders/*.csv)
       └─ Lambda (validate_and_trigger)
            └─ Glue Job (job1)
```
