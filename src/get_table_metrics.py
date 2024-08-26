#!/usr/bin/env python3
#
# Copyright 2024. Clumio, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Google Style 4 spaces, 100 columns:
#   https://google.github.io/styleguide/pyguide.html
#

"""Script to output metrics for DynamoDB tables.

The script saves the following metrics for each DynamoDB table to a CSV file:
- Table Size Bytes
- Item Count
- Avg Item Size Bytes
- Avg Daily WCU
- Avg Daily Change Rate
- Avg Daily Change Bytes

It expects the user to be logged in to AWS in some form, before running the script.
For the Avg Daily WCU, events of recent 14 days will be considered.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import math
import sys
from typing import TYPE_CHECKING, Any, Final, Sequence

import boto3
import botocore.exceptions

if TYPE_CHECKING:
    from mypy_boto3_cloudwatch import CloudWatchClient
    from mypy_boto3_dynamodb import DynamoDBServiceResource

DATA_PERIOD_IN_DAYS: Final = 14


def get_table_metrics(
    table_name: str, cloudwatch: CloudWatchClient, dynamodb: DynamoDBServiceResource
) -> dict[str, Any] | None:
    """Fetches table metrics from DynamoDB. Returns None on errors."""
    try:
        table = dynamodb.Table(table_name)
        table.load()

        table_size_bytes = table.table_size_bytes
        table_item_count = table.item_count
        table_avg_item_size_bytes = table_size_bytes / table_item_count if table_item_count else 0

        end_time = datetime.datetime.now(datetime.timezone.utc)
        start_time = end_time - datetime.timedelta(days=DATA_PERIOD_IN_DAYS)

        metrics = cloudwatch.get_metric_statistics(
            Namespace='AWS/DynamoDB',
            MetricName='ConsumedWriteCapacityUnits',
            Dimensions=[{'Name': 'TableName', 'Value': table_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum'],
        )

        # table_avg_daily_wcu denotes the average daily WCUs of recent DATA_PERIOD_IN_DAYS days
        if metrics['Datapoints']:
            table_total_wcu = sum(datapoint['Sum'] for datapoint in metrics['Datapoints'])
            table_avg_daily_wcu = table_total_wcu / DATA_PERIOD_IN_DAYS
        else:
            table_avg_daily_wcu = 0

        # x WCU is required to write a payload of x KB
        # wcu_needed_to_update_one_row denotes the number of WCU units required
        # to write an item of table_avg_item_size_bytes Bytes.
        # Please refer to the following link for more information:
        # https://aws.amazon.com/dynamodb/pricing/provisioned/?nc1=h_ls
        wcu_needed_to_update_one_row = (
            math.ceil(table_avg_item_size_bytes / 1024) if table_avg_item_size_bytes else 1
        )
        size_based_on_avg_daily_wcu = (
            table_avg_daily_wcu * table_avg_item_size_bytes / wcu_needed_to_update_one_row
        )
        table_avg_daily_change_rate = (
            size_based_on_avg_daily_wcu / table_size_bytes if table_size_bytes else 0
        )
        table_avg_daily_change_rate_percent = table_avg_daily_change_rate * 100

        return {
            'TableName': table_name,
            'TableSizeBytes': table_size_bytes,
            'ItemCount': table_item_count,
            'AvgItemSizeBytes': table_avg_item_size_bytes,
            'AvgDailyWCU': table_avg_daily_wcu,
            'AvgDailyChangeRate': f'{table_avg_daily_change_rate_percent:.2f}%',
            'AvgDailyChangeBytes': size_based_on_avg_daily_wcu,
        }

    except botocore.exceptions.ClientError as error:
        print(f'Error getting metrics for table {table_name}: {error}')
        if error.response['Error']['Code'] != 'ResourceNotFoundException':
            raise
        return None


def main(argv: Sequence[str]) -> int:
    """Main function."""
    parser = argparse.ArgumentParser(description='Get DynamoDB table metrics')
    parser.add_argument('--region', required=True, help='AWS region, e.g. us-west-2')
    parser.add_argument('--tables', nargs='*', help='Specific table names to get metrics for')
    parser.add_argument('--output', default='dynamodb_metrics.csv', help='Output CSV file path')
    args = parser.parse_args()

    session = boto3.Session(region_name=args.region)
    dynamodb = session.resource('dynamodb')
    cloudwatch = session.client('cloudwatch')

    # Get metrics for all tables if no specific tables are provided
    table_names = args.tables if args.tables else [table.name for table in dynamodb.tables.all()]

    with open(args.output, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'TableName',
            'TableSizeBytes',
            'ItemCount',
            'AvgItemSizeBytes',
            'AvgDailyWCU',
            'AvgDailyChangeRate',
            'AvgDailyChangeBytes',
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for table_name in table_names:
            metrics = get_table_metrics(table_name, cloudwatch, dynamodb)
            if metrics:
                writer.writerow(metrics)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
