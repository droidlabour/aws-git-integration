import os
import boto3
import json
import zipfile

from os.path import basename
from botocore.client import Config

cp = boto3.client('codepipeline')
s3 = boto3.client('s3', config=Config(signature_version='s3v4'))
cfn = boto3.client('cloudformation')


def get_templt_body(s):
    return json.dumps(cfn.get_template(StackName=s)['TemplateBody'])


def get_templt_param(s):
    x = cfn.describe_stacks(StackName=s)['Stacks'][0]['Parameters']
    p = dict()
    p['Parameters'] = dict()
    for i in x:
        if 'ECSTaskDesiredCount' == i['ParameterKey']:
            p['Parameters'][i['ParameterKey']] = os.getenv('ECSTaskDesiredCount')
        else:
            p['Parameters'][i['ParameterKey']] = i['ParameterValue']
    return json.dumps(p)


def handler(event, context):
    print event
    job_id = event['CodePipeline.job']['id']
    output_artifact_key = event['CodePipeline.job']['data']['outputArtifacts'][0]['location']['s3Location']['objectKey']
    output_artifact_bucket = event['CodePipeline.job']['data']['outputArtifacts'][0]['location']['s3Location']['bucketName']
    data = dict()
    templt_file = '/tmp/' + 'ecs_app.json'
    param_file = '/tmp/' + 'ecs_app_param.json'
    data[templt_file] = get_templt_body(os.getenv('AppStackName'))
    data[param_file] = get_templt_param(os.getenv('AppStackName'))
    try:
        os.remove('/tmp/templts.zip')
    except OSError:
        pass
    for i in data:
        with open(i, 'w') as f:
            f.write(data[i])
        with zipfile.ZipFile('/tmp/templts.zip', 'a') as z:
            z.write(i, basename(i))
    x = open('/tmp/templts.zip', 'rb')
    s3.put_object(Bucket=output_artifact_bucket, Key=output_artifact_key, Body=x, ServerSideEncryption='aws:kms', ContentType='application/zip')
    cp.put_job_success_result(jobId=job_id)
    return 0
