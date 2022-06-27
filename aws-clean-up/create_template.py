import boto3

ses = boto3.client('ses')
response = ses.delete_template(
    TemplateName='CCOECleanup'
)

f = open('./index.html')

response = ses.create_template(
  Template = {
    'TemplateName' : 'CCOECleanup',
    'SubjectPart'  : 'AWS cleanup',
    'TextPart'     : '',
    'HtmlPart'     : f.read()
  }
)


print(response)