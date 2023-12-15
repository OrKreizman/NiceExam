import json
import boto3
from datetime import datetime

def lambda_handler(event, context):
    bucket_name = event['bucket name'] if 'bucket name' in event else 'niceexambucket'
    s3_client = boto3.client('s3')
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    if response and 'Contents' in response:
        objects = response['Contents']
        objects = json.dumps([obj['Key'] for obj in objects])
    else:
        objects = f'No objects found in bucket{bucket_name}'
    cur_time = datetime.now().strftime("%b %d, %Y %H:%M:%S")
    s3_client.put_object(Body=objects.encode('utf-8'), Bucket=bucket_name, Key=f'bucket_objects_at:{cur_time}.json')
    return {
        'statusCode': 200,
        'body': json.dumps(objects)
    }
