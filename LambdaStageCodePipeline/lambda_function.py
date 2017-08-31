import os
import boto3
import json
import zipfile

from os.path import basename
from botocore.client import Config

codepipeline = boto3.client('codepipeline')
s3 = boto3.client('s3', config=Config(signature_version='s3v4'))
cfn = boto3.client('cloudformation')


def get_templt_body(s):
    b = cfn.get_template(StackName=s)['TemplateBody']
    if isinstance(b, str):
        return b
    else:
        return json.dumps(b)


def get_templt_param(s):
    stack_params = cfn.describe_stacks(StackName=s)['Stacks'][0]['Parameters']
    p = dict()
    p['Parameters'] = dict()
    for i in stack_params:
        if i['ParameterKey'] == 'ECSTaskDesiredCount' and i['ParameterValue'] == '0':
            p['Parameters'][i['ParameterKey']] = os.getenv('ECSTaskDesiredCount')
        else:
            p['Parameters'][i['ParameterKey']] = i['ParameterValue']
    return json.dumps(p)


def handler(event, context):
    print event
    job_id = event['CodePipeline.job']['id']
    output_artifact_key = event['CodePipeline.job']['data']['outputArtifacts'][0]['location']['s3Location']['objectKey']
    output_artifact_bucket = event['CodePipeline.job']['data']['outputArtifacts'][0]['location']['s3Location']['bucketName']
    artifact_files = {}
    artificat_pkg_file_name = '/tmp/templts.zip'
    artifact_files['/tmp/ecs_app.json'] = get_templt_body(os.getenv('ECSAPPStackName'))
    artifact_files['/tmp/ecs_app_param.json'] = get_templt_param(os.getenv('ECSAPPStackName'))

    try:
        print 'Removing ' + artificat_pkg_file_name
        os.remove(artificat_pkg_file_name)
    except OSError:
        pass

    for i in artifact_files:
        with open(i, 'w') as f:
            print 'Writing ' + i
            f.write(artifact_files[i])
        with zipfile.ZipFile(artificat_pkg_file_name, 'a') as z:
            z.write(i, basename(i))
    x = open(artificat_pkg_file_name, 'rb')
    s3.put_object(Bucket=output_artifact_bucket, Key=output_artifact_key, Body=x, ServerSideEncryption='aws:kms', ContentType='application/zip')
    codepipeline.put_job_success_result(jobId=job_id)
    return 0
