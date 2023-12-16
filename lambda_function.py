import json
import boto3, botocore
from datetime import datetime


def check_bucket_exists_and_accessible(bucket_name):
    """
    Checks the existence and accessibility of an AWS S3 bucket.
    :param name of the bucket to be checked
    :return: True if the bucket exists and is accessible, False otherwise
    """
    s3 = boto3.resource('s3')
    try:
        s3.meta.client.head_bucket(Bucket=bucket_name)
        return True
    except (botocore.exceptions.ClientError, botocore.exceptions.ParamValidationError) as e:
        # 403 for private 404 does not exist
        return False


def list_bucket_objects(bucket_name):
    """
    List all objects in a given S3 bucket.
    :param bucket_name: The name of the s3 bucket
    :return:all objects in a given S3 bucket
    """
    s3_resource = boto3.resource('s3')
    given_bucket = s3_resource.Bucket(bucket_name)
    if not check_bucket_exists_and_accessible(bucket_name): return {'statusCode': 400, 'body': json.dumps(
        'The given bucket does not exist')}
    objects_keys = [obj.key for obj in given_bucket.objects.all()]
    if len(objects_keys) == 0:  # bucket is empty
        objects_keys = [f'No objects found in bucket: {bucket_name}']
    return {
        'statusCode': 200,
        'body': json.dumps(objects_keys)
    }


def store_input_output(bucket_name, storing_bucket_name, response):
    """
    Storing input/output data into the bucket <storing_bucket_name>
    :param bucket_name: The given bucket (input)
    :param storing_bucket_name: Bucket to store the data in
    :param objects_keys: The given bucket objects (output)
    :return:
    """
    objects_keys = response['body']
    s3_resource = boto3.resource('s3')
    storing_bucket = s3_resource.Bucket(storing_bucket_name)
    if not check_bucket_exists_and_accessible(storing_bucket_name): return {'statusCode': 400, 'body': json.dumps(
        'The storing bucket does not exist')}
    cur_time = datetime.now().strftime("%b %d, %Y %H:%M:%S")  # give each object name that includes his creation time
    new_object_name = f'list objects from {bucket_name}, at:{cur_time}.json'
    storing_bucket.put_object(Key=new_object_name, Body=objects_keys)
    return response


def lambda_handler(event, context):
    """
    Lambda function to list objects from an S3 bucket and store them
    :param event: Dictionary containing information about the event that triggered the function.
                   Needs to contain 'bucket_name' key.
                   Optional: 'storing_bucket_name' key for the storing bucket name.
    :param context: AWS Lambda Context object.
    :return: Dictionary containing the HTTP status code and the list of object keys.
    """

    bucket_name = event.get('bucket_name', '')
    storing_bucket_name = event.get('storing_bucket_name', 'storing.lambda.input.output')
    response = list_bucket_objects(bucket_name)
    if not response['statusCode'] == 200: return response
    response = store_input_output(bucket_name, storing_bucket_name, response)
    return response
