import boto3
import random

def get_message_from_sqs():
    sqs = boto3.client('sqs',region_name="us-east-1")
    queue_url = 'https://YourOwnSQS_URL'

    # Receive message from SQS queue
    response = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=[
            'SentTimestamp'
        ],
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    )

    data = dict()
    if 'Messages' in response:
        message = response['Messages'][0]
        receipt_handle = message['ReceiptHandle']


        attr = ['Cuisine','Date','Location','NumberOfPeople','PhoneNumber','Time']
        for value in attr:
            data[value] = message['MessageAttributes'][value]['StringValue']


        # Delete received message from queue

        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )

        return [True,data]
    else:
        print('no message')
        return [False,data]





def send_sms_message(PhoneNumber, message):
    # Create an SNS client
    sns = boto3.client('sns')

    # Send a SMS message to the specified phone number
    response = sns.publish(
        PhoneNumber=PhoneNumber,
        Message=message,
    )


def get_message_from_es(Cuisine):
    from elasticsearch import Elasticsearch, RequestsHttpConnection
    from requests_aws4auth import AWS4Auth

    host = 'YourOwnElasticSearchHostName' # For example, my-test-domain.us-east-1.es.amazonaws.com
    region = 'us-east-1' # e.g. us-west-1

    service = 'es'
    #credentials = boto3.Session().get_credentials()
    #print(credentials)
    awsauth = AWS4Auth('YourOwnCredential', 'YourOwnCredential', region, service, session_token=None)

    es = Elasticsearch(
        hosts = [{'host': host, 'port': 443}],
        http_auth = awsauth,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )

    res = es.search(index='restaurants', doc_type='Restaurant', body={"query": {"match":{"cuisine": Cuisine}}})

    ids = []
    for i in range(3):
        num = random.randint(0,len(res['hits']['hits'])-1)
        id = res['hits']['hits'][num]['_source']['id']
        while id in ids:
            num = random.randint(0,len(res['hits']['hits'])-1)
            id = res['hits']['hits'][num]['_source']['id']
        ids.append(id)

    #id = res['hits']['hits'][0]['_source']['id']
    return ids


def get_message_from_db(id):
    dynamodb = boto3.resource('dynamodb')

    table = dynamodb.Table('yelp-restaurants')

    resp = table.get_item(Key={'id' : id})
    if 'Item' in resp:
        return resp['Item']

def lambda_handler(event, context):

    flag,data = get_message_from_sqs()
    #print(data)
    if flag == False:
        return
    Cuisine = data['Cuisine']
    NumberOfPeople = data['NumberOfPeople']
    Date = data['Date']
    Time = data['Time']

    # get_message_from_es
    ids = get_message_from_es(Cuisine)

    # get_message_from_db
    names = []
    addresses = []
    for id in ids:
        res = get_message_from_db(id)
        name = res['name']
        names.append(name)
        address = res['address']
        addresses.append(address)
    sug = ""
    for i in range(len(names)):
        sug += str(i+1) + ". "
        sug += names[i]
        sug += " "
        sug += addresses[i]
        sug += " "
    message = 'Hello! Here are my ' + Cuisine + ' restaurant suggestions for ' + NumberOfPeople + ' people, for '+ Date +' at '+ Time +': '+ sug +'. Enjoy your meal!'
    print(message)

    PhoneNumber = '+1' + data['PhoneNumber']
    send_sms_message(PhoneNumber,message)
