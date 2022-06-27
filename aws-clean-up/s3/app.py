import boto3
import json
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CLEANUP_TAG = 'JBL:CCOE_CLEANUP'
CLEANUP_VALUE = 'FALSE'
FILTER_CCOE_CLEANUP_TAG = lambda item: item['Key'].upper() == CLEANUP_TAG and item['Value'].upper() == CLEANUP_VALUE
PREFIX_SUBJECT = 'AWS CLEANUP'
RECIPIENTS = [ 'isai_cruz@jabil.com' ]
SOURCE = 'isai_cruz@jabil.com'
TEMPLATE = 'CCOECleanup'

client = boto3.client('s3')
s3 = boto3.resource('s3')
ses_client = boto3.client('ses')

def send_email(deleted , skipped):
    try:
        resources = {
            'resource':'S3',
            'skipped': skipped,
            'deleted': deleted,
            'error':''
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


#empty and delete buckets
def lambda_handler(event, context):
    try:
        deleted = []
        skipped = []
        f = open('./exceptions.json')
        data = json.load(f)
        f.close()
        s3_exceptions = []
        #upper all buckets
        for resource in data['buckets']:
            s3_exceptions.append(resource.upper())

        response = client.list_buckets()

        for bucket in response['Buckets']:
            bucket_name = bucket['Name']
            try:
                response_tagging = client.get_bucket_tagging(
                    Bucket=bucket_name
                )
            except:
                response_tagging = { 'TagSet':[] }
            tags = response_tagging['TagSet']
            filtered_tags = list(filter(FILTER_CCOE_CLEANUP_TAG,tags))
            if len(filtered_tags) > 0:
                logger.info('Skip bucket:'+bucket_name)
                skipped.append( {'resource':bucket_name })
                continue
            deleted.append({'resource':bucket_name })
            s3_bucket = s3.Bucket(bucket_name)
            logger.info('Delete bucket:'+bucket_name)
            bucket_versioning = s3.BucketVersioning(bucket_name)
            if bucket_versioning.status == 'Enabled':
                s3_bucket.object_versions.delete()
            else:
                s3_bucket.objects.all().delete()
            s3_bucket.delete()
        send_email(deleted,skipped)
    except:
        raise