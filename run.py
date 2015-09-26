from flask import Flask, request, redirect, session, render_template
from twilio.rest import TwilioRestClient 
import twilio.twiml

from flask import g, url_for, flash
from flask_oauthlib.client import OAuth

 
# put your own credentials here 
ACCOUNT_SID = "AC88218c95eb28488e2e09a3e11f5e41f0" 
AUTH_TOKEN = "26186a1b74c792f7e6cbfa64f39db691" 
 
client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN) 

app = Flask(__name__)
app.config.from_object(__name__)
app.debug = True
oauth = OAuth(app)
# app.config.from_pyfile('local_settings.py')

users = []

@app.route('/')
def landingpage():
	return render_template('index.html', name = __name__)
	# return "hello"

@app.route('/signup', methods = ['POST'])
def signup():
	name = request.form['name']
	phone = request.form['phone']
	email = True if request.form.get('email')!=None else False
	facebook = True if request.form.get('facebook')!=None else False
	twitter = True if request.form.get('twitter')!=None else False


	features = ("EMAIL" if email else "") + (" FACEBOOK" if facebook else "") + ("TWITTER" if twitter else "")  

	message = client.messages.create(body="Hi " + name + ", welcome to Uiwi! You enabled "+ features + " features. Text the feature name to get instructions!",
    to="+1"+phone,    # Replace with your phone number
    from_="+12564327214") # Replace with your Twilio number

	# print("The  is '" + phone + "'" + " for " + name+","+email+facebook+str(twitter))
	return redirect('/')

if __name__ == '__main__':
    app.run()



