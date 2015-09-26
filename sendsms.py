# We are using the RESTful API provided by Twilio
from twilio.rest import TwilioRestClient

# Account ID and authentication token from https://www.twilio.com/user/account
account_sid = "ACba6adc0042509e7ced6d2bbbb700b8e6"
auth_token = "c51fd911c53fde73d78848b3f1bd4ca7"
client = TwilioRestClient(account_sid, auth_token)

# NOTE: Must send from Twilio trial number to Twilio validated cell
# Sending an MMS is the same as sending an SMS with the addition of the media_url param
client.messages.create(to = "+12145347832", from_= "+14695072796",
	body="Hello, Austin!",
	media_url = ["http://www.whenwasitinvented.org/wp-content/uploads/2011/12/Frisbee.jpg"])

