import boto3
import json
import logging 
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)  

CLEANUP_TAG = 'JBL:CCOE_CLEANUP'
CLEANUP_VALUE = 'FALSE'
FILTER_CCOE_CLEANUP_TAG = lambda item: item[0].upper() == CLEANUP_TAG and item[1].upper() == CLEANUP_VALUE
PREFIX_SUBJECT = 'AWS CLEANUP'
RECIPIENTS = [ 'isai_cruz@jabil.com' ]
SOURCE = 'isai_cruz@jabil.com'
TEMPLATE = 'CCOECleanup'

REGIONS = [
    'us-east-1',
    'us-east-2',
]
ses_client = boto3.client('ses')

def send_email(deleted , skipped):
    try:
        resources = {
            'resource':'Lambda',
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

def lambda_handler(event, context):
    try:
        f = open('./exceptions.json')
        data = json.load(f)
        f.close()
        lambda_exceptions = []    
        layer_exceptions = []
        #upper all layers
        for layer in data['layers']:
            layer_exceptions.append(layer.upper())
        #upper all functions
        for resource in data['functions']:
            lambda_exceptions.append(resource.upper())
        
        deleted_resources = []
        skipped_resources = []

        for region in REGIONS:
            client = boto3.client('lambda', region_name=region)
            response = { 'NextMarker':''}
            deleted_functions = []
            while 'NextMarker' in response:
                if response['NextMarker'] == '':
                    response = client.list_functions(
                        FunctionVersion='ALL',
                        MaxItems=50
                    )
                else:    
                    response = client.list_functions(
                        FunctionVersion='ALL',
                        MaxItems=50,
                        NextMarker=next_marker
                    )

                functions = response['Functions']
                for function in functions:
                    function_name = function['FunctionName']
                    function_arn = function['FunctionArn']
                    last_index = function_arn.rfind(':')
                    function_arn = function_arn[0:last_index]
                    tags_response = client.list_tags(Resource=function_arn)                    
                    filtered_tags = list(filter(FILTER_CCOE_CLEANUP_TAG,tags_response['Tags'].items()))
                    if len(filtered_tags) > 0:
                        skipped_resources.append({'resource':f'[{region}][Lambda] ->'+function_name })
                        logger.info('Skip function: '+ function_name )
                        continue 
                    deleted_resources.append({'resource':f'[{region}][Lambda] ->'+function_name })
                    logger.info('Delete function: '+ function_name )
                    if not(function_name  in deleted_functions):
                        response = client.delete_function(
                            FunctionName=function_name
                        )
                        deleted_functions.append(function_name)
                        
            
            response = { 'NextMarker':''}
            while 'NextMarker' in response:
                if response['NextMarker'] == '':
                    response = client.list_layers(
                        MaxItems=50
                    )
                else:    
                    response = client.list_layers(
                        MaxItems=50,
                        NextMarker=next_marker
                    )
                
                layers = response['Layers']
                for layer in layers:
                    layer_name = layer['LayerName']
                    if not(layer_name.upper() in layer_exceptions):
                        response_versions = client.list_layer_versions(LayerName=layer_name)
                        for layer_version in response_versions['LayerVersions']:
                            version = layer_version['Version']
                            logger.info('Delete layer version: '+layer_name+':'+str(version))
                            deleted_resources.append({'resource': f'[{region}][Layer] ->'+layer_name })
                            client.delete_layer_version(LayerName=layer_name,VersionNumber=version)
                    else:
                        skipped_resources.append({'resource':f'[{region}][Layer] ->'+layer_name })
                        logger.info('Skip layer : '+layer_name)
        send_email(deleted_resources,skipped_resources)
    except:
        raise
