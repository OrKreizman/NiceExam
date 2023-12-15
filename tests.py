import unittest
import boto3
import json

class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.lambda_name = 'listS3BucketObjects'
        self.lambda_client = boto3.client('lambda','eu-west-1')
        # self.s3_client = boto3.client('s3')
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
        # response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
        # return [obj['Key'] for obj in response['Contents']]

    def test_empty_bucket(self):
        # delete all objects from testing bucket
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(self.bucket_name)
        for obj in bucket.objects.all():
            obj.delete()
        expected_response = {
        'statusCode': 200,
        'body': json.dumps([f'No objects found in bucket{self.bucket_name}'])
        }
        response = self.invoke_lambda()
        self.assertDictEqual(expected_response,response)


    def test_lambda_response(self):
        objects = self.get_objects_keys()
        response_data = self.invoke_lambda()
        expected_returned_data = json.dumps(objects)
        self.assertEqual(200,response_data['statusCode'])
        self.assertEqual(response_data['body'],expected_returned_data)


    def test_s3_saved_data(self):
        expected_objects = self.invoke_lambda()['body']
        added_object_key = max(self.get_objects_keys())
        added_object = self.bucket.Object(added_object_key).get()
        object_data = added_object['Body'].read().decode()
        self.assertEqual(object_data, expected_objects)


if __name__ == '__main__':
    unittest.main()
