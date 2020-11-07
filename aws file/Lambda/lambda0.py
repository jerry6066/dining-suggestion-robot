import json

def lambda_handler(event, context):
    # TODO implement

    inputMessage = event['messages'][0]['unstructured']['text']

    import boto3
    client = boto3.client('lex-runtime')
    lexResponse = client.post_text(
        botName='DiningChatBot',
        botAlias='one',
        userId='John',
        sessionAttributes={
            #'string': 'string'
        },
        requestAttributes={
            #'string': 'string'
        },
        inputText=inputMessage
    )
    response = {
        'headers': {'Access-Control-Allow-Origin': '*'},
        'messages': [ {
            'type': "unstructured",
            'unstructured': {
                'text': lexResponse['message']
            }
        } ]
    }

    return response
