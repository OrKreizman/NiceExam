import json
import unittest
from moto import mock_s3
import boto3
from lambda_function import lambda_handler


class TestLambdaHandler(unittest.TestCase):
    """
    Class for testing the function lambda_handler
    """

    @mock_s3
    def setUp(self):
        self.given_bucket_name = 'my.tests.bucket'
        self.storing_bucket_name = 'storing.lambda.input.output'
        self.s3 = boto3.resource('s3')

    @mock_s3
    def test_invalid_buckets_names(self):
        """
        Test for invalid AWS S3 bucket names.
        :return:
        """
        invalid_bucket_name_event = {'bucket_name': ''}
        invalid_storing_bucket_name_event = {'bucket_name': self.given_bucket_name, 'storing_bucket_name': ''}
        self.s3.create_bucket(Bucket=self.given_bucket_name)
        self.assertEqual(400, lambda_handler(invalid_bucket_name_event, None)['statusCode'])
        self.assertEqual(400, lambda_handler(invalid_storing_bucket_name_event, None)['statusCode'])

    @mock_s3
    def test_lambda_with_empty_bucket(self):
        """
        Test the response of the lambda function for empty bucket (0 objects).
        :return:
        """
        # creating buckets for test
        self.s3.create_bucket(Bucket=self.given_bucket_name)
        self.s3.create_bucket(Bucket=self.storing_bucket_name)

        event = {'bucket_name': self.given_bucket_name}
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        # check if response body is as expected (a list with the message about ampty bucket)
        expected_response = [f'No objects found in bucket: {self.given_bucket_name}']
        self.assertEqual(response_body, expected_response)

    @mock_s3
    def test_lambda_response(self):
        """
        Test Lambda function response for a specified S3 bucket.
        :return:
        """
        # creating buckets for test
        self.s3.create_bucket(Bucket=self.storing_bucket_name)
        bucket = self.s3.create_bucket(Bucket=self.given_bucket_name)
        # adding the given bucket some objects for the test
        objects_names = [f'example_object_{i}.txt' for i in range(3)]
        for obj in objects_names:
            bucket.put_object(Key=obj, Body=b'content')

        event = {'bucket_name': self.given_bucket_name}
        response = lambda_handler(event, None)
        objects_keys = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 200)
        self.assertTrue(objects_names, objects_keys)


class TestIntegration(unittest.TestCase):
    """
    Class for testing the lambda integration.
    Contacting with the aws lambda with the name <self.lambda_name>
    """

    def setUp(self):
        """
        Initial necessaries variables for testing
        :return: None
        """
        self.lambda_name = 'listS3BucketObjects'
        self.lambda_client = boto3.client('lambda', 'eu-west-1')
        self.bucket_name = 'my.tests.bucket'
        s3_resource = boto3.resource('s3')
        self.bucket = s3_resource.Bucket(self.bucket_name)

    def invoke_lambda(self):
        """
        Invoke an AWS Lambda function and retrieve the JSON response.
        :return:
        """
        event = {'bucket_name': self.bucket_name,
                 'storing_bucket_name': self.bucket_name
                 }
        response = self.lambda_client.invoke(
            FunctionName=self.lambda_name,
            InvocationType='RequestResponse',  # Can be 'Event' for asynchronous invocation
            Payload=json.dumps(event)
        )
        return json.loads(response['Payload'].read())

    def get_objects_keys(self):
        """
        Get keys of all objects within the given S3 bucket (self.bucket).
        :return:
        """
        return [obj.key for obj in self.bucket.objects.all()]

    def test_empty_bucket(self):
        """
        Test the response of the lambda for empty bucket (0 objects).
        :return:
        """
        # delete all objects from the testing bucket
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(self.bucket_name)
        bucket.objects.all().delete()
        expected_response = {
            'statusCode': 200,
            'body': json.dumps([f'No objects found in bucket: {self.bucket_name}'])
        }
        response = self.invoke_lambda()
        self.assertDictEqual(expected_response, response)

    def test_lambda_response(self):
        """
        Test that the lambda returns the expected response for s3 bucket with objects.
        the expected response is list with all objects keys in the given S3 bucket
        :return:
        """
        # create an object to make sure bucket isn't empty
        obj_key = 'testing object_object.txt'
        self.bucket.put_object(Key=obj_key, Body=b'content')
        objects = self.get_objects_keys()
        response_data = self.invoke_lambda()
        expected_returned_data = json.dumps(objects)
        self.assertEqual(200, response_data['statusCode'])
        self.assertEqual(response_data['body'], expected_returned_data)
        # delete added object
        self.bucket.Object(obj_key).delete()

    def test_s3_saved_data(self):
        """
        Test the data saved in an S3 bucket matches the expected data after invoking a Lambda function.
        :return:
        """
        expected_objects = self.invoke_lambda()['body']
        added_object_key = max(self.get_objects_keys())
        added_object = self.bucket.Object(added_object_key).get()
        object_data = added_object['Body'].read().decode()
        self.assertEqual(object_data, expected_objects)


if __name__ == '__main__':
    unittest.main()
