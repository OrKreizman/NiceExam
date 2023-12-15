import json
import unittest
from moto import mock_s3
import boto3
from lambda_function import lambda_handler


class TestLambdaHandler(unittest.TestCase):

    @mock_s3
    def setUp(self):
        self.bucket_name = 'bucket'
        self.s3 = boto3.resource('s3')

    @mock_s3
    def test_lambda_with_empty_bucket(self):
        self.s3.create_bucket(Bucket=self.bucket_name)
        event = {'bucket name': self.bucket_name}
        response = lambda_handler(event, None)
        # check if statusCode is OK
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        # check if response body is as expected (a list with the message about ampty bucket)
        expected_response = [f'No objects found in bucket{self.bucket_name}']
        self.assertEqual(response_body, expected_response)

    @mock_s3
    def test_lambda_response(self):
        bucket = self.s3.create_bucket(Bucket=self.bucket_name)
        objects_names = [f'example_object_{i}.txt' for i in range(3)]
        for obj in objects_names:
            bucket.put_object(Key=obj, Body=b'content')
        event = {'bucket name': self.bucket_name}
        response = lambda_handler(event, None)
        objects_keys = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 200)
        self.assertTrue(objects_names, objects_keys)


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.lambda_name = 'listS3BucketObjects'
        self.lambda_client = boto3.client('lambda', 'eu-west-1')
        self.bucket_name = 'my.tests.bucket'
        s3_resource = boto3.resource('s3')
        self.bucket = s3_resource.Bucket(self.bucket_name)

    def invoke_lambda(self):
        event = {'bucket name': self.bucket_name}
        response = self.lambda_client.invoke(
            FunctionName=self.lambda_name,
            InvocationType='RequestResponse',  # Can be 'Event' for asynchronous invocation
            Payload=json.dumps(event)
        )
        return json.loads(response['Payload'].read())

    def get_objects_keys(self):
        return [obj.key for obj in self.bucket.objects.all()]

    def test_empty_bucket(self):
        # delete all objects from testing bucket
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(self.bucket_name)
        bucket.objects.all().delete()
        expected_response = {
            'statusCode': 200,
            'body': json.dumps([f'No objects found in bucket{self.bucket_name}'])
        }
        response = self.invoke_lambda()
        self.assertDictEqual(expected_response, response)

    def test_lambda_response(self):
        objects = self.get_objects_keys()
        response_data = self.invoke_lambda()
        expected_returned_data = json.dumps(objects)
        self.assertEqual(200, response_data['statusCode'])
        self.assertEqual(response_data['body'], expected_returned_data)

    def test_s3_saved_data(self):
        expected_objects = self.invoke_lambda()['body']
        added_object_key = max(self.get_objects_keys())
        added_object = self.bucket.Object(added_object_key).get()
        object_data = added_object['Body'].read().decode()
        self.assertEqual(object_data, expected_objects)


if __name__ == '__main__':
    unittest.main()
