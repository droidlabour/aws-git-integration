import os
import logging
import traceback
import cfnresponse

import boto3

log = logging.getLogger()
log.setLevel('DEBUG')


def deploy(event, context):
    client = boto3.client('codedeploy', os.getenv('region'))
    log.debug('Event is %s', event)
    response = client.create_deployment(
        applicationName=os.getenv('application_name'),
        deploymentGroupName=os.getenv('deployment_group'),
        revision={
           'revisionType': 'S3',
           's3Location': {
               'bucket': os.getenv('s3_bucket'),
               'key': os.getenv('s3_key'),
               'bundleType': 'zip'
           }
        },
        ignoreApplicationStopFailures=True
    )
    log.debug('Create deployment response %s', response)


def add_s3_notification(event, context):
    try:
        client = boto3.client('s3')
        log.debug('Event is %s', event)
        existing_notifications = client.get_bucket_notification_configuration(
            Bucket=os.getenv('s3_bucket')
        )
        new_notifications = dict()
        if 'TopicConfigurations' in existing_notifications.keys():
            new_notifications['TopicConfigurations'] = existing_notifications['TopicConfigurations']
        if 'QueueConfigurations' in existing_notifications.keys():
            new_notifications['QueueConfigurations'] = existing_notifications['QueueConfigurations']
        if 'LambdaFunctionConfigurations' in existing_notifications.keys():
            new_notifications['LambdaFunctionConfigurations'] = existing_notifications['LambdaFunctionConfigurations']
            for k, v in enumerate(existing_notifications['LambdaFunctionConfigurations']):
                if v['LambdaFunctionArn'] == os.getenv('lambda_arn'):
                    log.info('Bucket notification already exists %s', v)
                    key_to_delete = k
        else:
            new_notifications['LambdaFunctionConfigurations'] = []
        if event['RequestType'] == 'Create':
            new_notification = {
                'LambdaFunctionArn': os.getenv('lambda_arn'),
                'Events': ['s3:ObjectCreated:*'],
                'Filter': {
                    'Key': {
                        'FilterRules': [
                            {
                                'Name': 'prefix',
                                'Value': os.path.dirname(os.getenv('s3_key')) + '/'
                            },
                            {
                                'Name': 'suffix',
                                'Value': '.zip'
                            }
                        ]
                    }
                }
            }
            log.info('Creating new bucket notification %s', new_notification)
            new_notifications['LambdaFunctionConfigurations'].append(new_notification)
            client.put_bucket_notification_configuration(
                Bucket=os.getenv('s3_bucket'),
                NotificationConfiguration=new_notifications
            )
        elif event['RequestType'] == 'Update':
            new_notification = {
                'LambdaFunctionArn': os.getenv('lambda_arn'),
                'Events': ['s3:ObjectCreated:*'],
                'Filter': {
                    'Key': {
                        'FilterRules': [
                            {
                                'Name': 'prefix',
                                'Value': os.path.dirname(os.getenv('s3_key')) + '/'
                            },
                            {
                                'Name': 'suffix',
                                'Value': '.zip'
                            }
                        ]
                    }
                }
            }
            log.info('Updating with new bucket notification %s', new_notification)
            new_notifications['LambdaFunctionConfigurations'].pop(key_to_delete)
            new_notifications['LambdaFunctionConfigurations'].append(new_notification)
            client.put_bucket_notification_configuration(
                Bucket=os.getenv('s3_bucket'),
                NotificationConfiguration=new_notifications
            )
        elif event['RequestType'] == 'Delete':
            new_notifications['LambdaFunctionConfigurations'].pop(key_to_delete)
            log.info('Deleting bucket notification %s', new_notifications['LambdaFunctionConfigurations'])
            client.put_bucket_notification_configuration(
                Bucket=os.getenv('s3_bucket'),
                NotificationConfiguration=new_notifications
            )
        else:
            log.info('Skipping as Cloudformation status is %s', event['RequestType'])
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {}, '')
    except:
        print traceback.print_exc()
        cfnresponse.send(event, context, cfnresponse.FAILED, {}, '')
