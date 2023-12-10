import rsa
import os
import functools
import boto3
from botocore.exceptions import ClientError
from botocore.signers import CloudFrontSigner
from datetime import datetime, timedelta

key_id = os.environ['KEY_ID']
domain_name = os.environ['DOMAIN_NAME']
secret_name = os.environ['SECRET_NAME']
expiry_time = os.environ['EXPIRY_TIME']
region_name = os.getenv("REGION", 'us-west-2')
s3_bucket = os.environ['S3_BUCKET']
session = boto3.Session(region_name=region_name)
clientSM = session.client('secretsmanager')
clientS3 = session.client('s3')

def get_secret():
    try:
        get_secret_value_response = clientSM.get_secret_value(
            SecretId=secret_name
        )
        return get_secret_value_response
    except ClientError as e:
        print(e)
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e

def checkFileExists(filename):
    try:
        get_s3_response = clientS3.head_object(Bucket=s3_bucket, Key=filename)
        get_s3_response = get_s3_response["ResponseMetadata"]["HTTPStatusCode"]
        return get_s3_response
    except ClientError as error:
        get_s3_response = error.response["Error"]["Code"]
        return get_s3_response

def lambda_handler(event, context):
    file_name = event['file_name']
    file_exists_response = checkFileExists(file_name)

    if file_exists_response != 200:
        file_error = f"File not found!"
        response = {
            'statusCode': file_exists_response,
            'body': file_error,
            'file-name': file_name
        }
        print("response: ", response)
        return response
    key_file = get_secret()
    key_file = key_file['SecretString']
    res = bytes(key_file, 'utf-8')

    url = f'https://{domain_name}/{file_name}'
    expire_at = datetime.now() + timedelta(seconds=int(expiry_time))

    priv_key = rsa.PrivateKey.load_pkcs1(res)
    rsa_signer = functools.partial(
        rsa.sign, priv_key=priv_key, hash_method='SHA-1'
    )

    cf_signer = CloudFrontSigner(key_id, rsa_signer)
    url = cf_signer.generate_presigned_url(url, date_less_than=expire_at)
    response = {
        'statusCode': 200,
        'headers': {
            'Location': url
        }
    }

    return response
