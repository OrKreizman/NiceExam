import json
import boto3
from datetime import datetime


def lambda_handler(event, context):
    bucket_name = event['bucket name'] if 'bucket name' in event else 'niceexambucket'
    s3_resource = boto3.resource('s3')
    bucket = s3_resource.Bucket(bucket_name)
    objects_keys = [obj.key for obj in bucket.objects.all()]
    if len(objects_keys) == 0:  # bucket is empty
        objects_keys = [f'No objects found in bucket{bucket_name}']
    objects_keys = json.dumps(objects_keys)

    # give each object name that includes his creation time
    cur_time = datetime.now().strftime("%b %d, %Y %H:%M:%S")
    new_object_name = f'bucket_objects_at:{cur_time}.json'

    bucket.put_object(Key=new_object_name, Body=objects_keys)

    return {
        'statusCode': 200,
        'body': objects_keys
    }