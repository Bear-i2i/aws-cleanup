import json
import logging
import boto3
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

PREFIX_SUBJECT = 'AWS CLEANUP'
RECIPIENTS = [ 'isai_cruz@jabil.com' ]
SOURCE = 'isai_cruz@jabil.com'
TEMPLATE = 'CCOECleanup'
ses_client = boto3.client('ses')

def send_email(error_message):
    try:
        resources = {
            'resource':'VPC',
            'skipped': [],
            'deleted': [],
            'error':error_message
        }
        now = datetime.now()
        subject = PREFIX_SUBJECT + now.strftime("%m/%d/%Y %H:%M:%S")
        response = ses_client.send_templated_email(
            Source=SOURCE,
            Destination={
                'ToAddresses': RECIPIENTS
            },
            Template=TEMPLATE,
            TemplateData=json.dumps(resources)
        )
        logger.info(response)
    except:
        raise


def lambda_handler(event, context):
    try:
        raise Exception("AWS VPC service is a method not implemented!")
    except Exception as err:
        logger.info(err)
        send_email(str(err))
        raise