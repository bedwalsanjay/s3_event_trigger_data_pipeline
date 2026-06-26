import sys
import pandas as pd
from datetime import datetime, timezone
from awsglue.utils import getResolvedOptions

args = getResolvedOptions(sys.argv, ["source_bucket", "source_key", "target_bucket"])

source_path = f"s3://{args['source_bucket']}/{args['source_key']}"
filename = args["source_key"].split("/")[-1]
target_path = f"s3://{args['target_bucket']}/processed/orders/{filename}"

df = pd.read_csv(source_path)

# Add ingestion timestamp
df["file_ingestion"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

# Remove duplicates
df = df.drop_duplicates()

# Remove milliseconds from order_date
df["order_date"] = pd.to_datetime(df["order_date"]).dt.strftime("%Y-%m-%d %H:%M:%S")

df.to_csv(target_path, index=False)
