import json
import math
import datetime
import dateutil.parser
import time
import os
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

""" --- helper function --- """
def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')

def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False

def get_slots(intent_request):
    return intent_request['currentIntent']['slots']

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }

def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def validate_suggestion(location,cuisine,numberOfPeople,est_date,est_time,phoneNumber):

    if location != None:
        # validate loction
        ava_location = ['manhattan']
        location = location.lower()
        if location not in ava_location:
            return build_validation_result(False,
                                           'Location',
                                           'Sorry about that, we only serve in Manhattan, Please type Manhattan')
    if cuisine != None:
        # validate cuisine
        ava_cuisine = ['chinese', 'japanese', 'korean', 'italian', 'mexican', 'american', 'indian']
        cuisine = cuisine.split(' ')[0].lower()
        if cuisine not in ava_cuisine:
            return build_validation_result(False,
                                           'Cuisine',
                                           'Sorry about that, we only have Chinese/Japanese/Korean/Italian/Mexican/American/In food. Which one do you want?')

    if numberOfPeople != None:
        # validate numberOfPeople
        if int(numberOfPeople) <= 0:
            return build_validation_result(False,
                                           'NumberOfPeople',
                                           'Try again please. I need a positive number.')

        if int(numberOfPeople) > 10:
            return build_validation_result(False,
                                           'NumberOfPeople',
                                           'Sorry, the restaurant only support 10 people at most.')

    # validate est_date
    if est_date is not None:
        if not isvalid_date(est_date):
            return build_validation_result(False, 'Date', 'I did not understand that, what date would you like?')
        elif datetime.datetime.strptime(est_date, '%Y-%m-%d').date() <= datetime.date.today():
            return build_validation_result(False, 'Date', 'You can order from tomorrow onwards.  What day would you like?')

    # validate est_time
    if est_time is not None:
        if len(est_time) != 5:
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'Time', "Please type a valid time")

        hour, minute = est_time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'Time', "Please type a valid time")

        if hour < 8 or hour > 22:
            # Outside of business hours
            return build_validation_result(False, 'Time', 'Our business hours are from eight a m. to ten p m. Can you specify a time during this range?')

    if phoneNumber != None:
        # validate phoneNumber
        if len(phoneNumber) != 10:
            return build_validation_result(False,
                                           'PhoneNumber',
                                           'Please type a valid phone number. I only support 10-digit number in US.')

    # o.w. return True
    return build_validation_result(True, None, None)

""" --- Intent behavior --- """

def greeting(intent_request):
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': "Hi there,how can I help?"})

def thank(intent_request):
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': "You're welcome."})

def diningSuggest(intent_request):


    location = get_slots(intent_request)["Location"]
    cuisine = get_slots(intent_request)["Cuisine"]
    numberOfPeople = get_slots(intent_request)["NumberOfPeople"]
    est_date = get_slots(intent_request)["Date"]
    est_time = get_slots(intent_request)["Time"]
    phoneNumber = get_slots(intent_request)["PhoneNumber"]

    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
        # validate the input
        slots = get_slots(intent_request)

        validation_result = validate_suggestion(location,cuisine,numberOfPeople,est_date,est_time,phoneNumber)
        if not validation_result['isValid']:
            # if something wrong with slot
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])

        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

        return delegate(output_session_attributes, get_slots(intent_request))

    # success

    # Create SQS client

    sqs = boto3.client('sqs',region_name="us-east-1")

    queue_url = 'https://ChangeItWithYourOwnSQS_URL'

    # Send message to SQS queue
    response = sqs.send_message(
        QueueUrl=queue_url,
        DelaySeconds=10,
        MessageAttributes={
            'Location': {
                'DataType': 'String',
                'StringValue': location
            },
            'Cuisine': {
                'DataType': 'String',
                'StringValue': cuisine
            },
            'NumberOfPeople': {
                'DataType': 'Number',
                'StringValue': numberOfPeople
            },
            'Date': {
                'DataType': 'String',
                'StringValue': est_date
            },
            'Time': {
                'DataType': 'String',
                'StringValue': est_time
            },
            'PhoneNumber': {
                'DataType': 'Number',
                'StringValue': phoneNumber
            }
        },
        MessageBody=(
            'This is test info.'
        )
    )

    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': " You’re all set. Expect my suggestions shortly! Have a good day."})

""" --- Analyze intent --- """

def dispatch(intent_request):

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'GreetingIntent':
        return greeting(intent_request)
    elif intent_name == 'ThankYouIntent':
        return thank(intent_request)
    elif intent_name == 'DiningSuggestionsIntent':
        return diningSuggest(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')




""" --- Main handler --- """

def lambda_handler(event, context):
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
