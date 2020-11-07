# Rebuild Project on AWS

Step 0: You need an AWS account before starting.

Step 1: Upload all files in ```S3``` folder, and make your S3 bucket as a host for static website.

(Important: Before uploading file, you must change line 56 in ```S3/assets/js/sdk/apigClient.js```. You should change it to your own URL for API Gateway in next step.)

Step 2: Use ```API Gateway/swagger.yaml``` to set up your API Gateway Service. (Remember to enable CORS.)

Step 3: Create a new Lambda Function called ```LF0```. Let your API Gateway to trigger it. You may copy the code in ```Lambda/lambda0.py``` to ```LF0```. 

Step 4: Create a Lex bot and add some intents or questions you want to ask users. Then use ```LF1``` in next step for initialization and fulfillment of you robot.

Step 5: Create a Lambda Function called ```LF1``` to initialize Lex bot and do some verification about user's input message. You may copy the code in ```Lambda/lambda1.py``` to ```LF1```. (You should change line 194 to your own SQS URL in next step.)

Step 5: Create a new SQS instance, which is used to store the necessary information about users.

Step 6: Create a new DynamoDB and ElasticSearch instance.

Step 7: Use ```Yelp.ipynb``` to get restaurant information and store the data into DyanamoDB and ElasticSearch. (You may need your own Yelp API key and ElasticSearch host name.)

Step 8: Create a new Lambda Function (LF2). You may copy the code in ```Lambda/lambda2.py``` to ```LF2```. (You should use your own AWS credentials)

Step 9: Step up a CloudWatch Event to trigger ```LF2``` every minute.

Step 10: All done. You can play with your own bot.



---

Reminder: During the whole steps, you need to set role or security group for some services properly. Also, you may want to look up the [official documentation](https://docs.aws.amazon.com/) for detail information about each service for AWS. Good luck!

