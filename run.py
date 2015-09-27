
from flask import Flask, request, redirect, session, render_template
from twilio.rest import TwilioRestClient 
import twilio.twiml

from flask import g, url_for, flash
from flask_oauthlib.client import OAuth

from flask import Flask, request, redirect, url_for, session, g, flash, \
     render_template
from flask_oauth import OAuth

import tweepy
from flask.ext.tweepy import Tweepy
 
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

 
# put your own credentials here 
ACCOUNT_SID = "AC88218c95eb28488e2e09a3e11f5e41f0" 
AUTH_TOKEN = "26186a1b74c792f7e6cbfa64f39db691" 



 
client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN) 

app = Flask(__name__)
app.config.from_object(__name__)
app.debug = True
app.secret_key = "development key"
oauth = OAuth()


auth = tweepy.OAuthHandler("pfN8ThAB7BRVxiLgwdNZGsZgx", 'KmoKfwtczF9feghCp9msCHr8lh0U7yfOPwdkuePrsku58yv54b')
auth.set_access_token('3008431471-HqHddaolepGh0QYf1eEGWtFctHP2g2FsjiNsH97', 'vQ1NAdYtsXd6aKIee38VNvsuhSUVo9G8gA4hi9TYRjPJq')
api = tweepy.API(auth)

# app.config.from_pyfile('local_settings.py')
# Use Twitter as example remote application
twitter = oauth.remote_app('twitter',
    # unless absolute urls are used to make requests, this will be added
    # before all URLs.  This is also true for request_token_url and others.
    base_url='https://api.twitter.com/1.1/',
    # where flask should look for new request tokens
    request_token_url='https://api.twitter.com/oauth/request_token',
    # where flask should exchange the token with the remote application
    access_token_url='https://api.twitter.com/oauth/access_token',
    # twitter knows two authorizatiom URLs.  /authorize and /authenticate.
    # they mostly work the same, but for sign on /authenticate is
    # expected because this will give the user a slightly different
    # user interface on the twitter side.
    authorize_url='https://api.twitter.com/oauth/authenticate',
    # the consumer keys from the twitter application registry.
    consumer_key='pfN8ThAB7BRVxiLgwdNZGsZgx',
    consumer_secret='KmoKfwtczF9feghCp9msCHr8lh0U7yfOPwdkuePrsku58yv54b'
)
 
@twitter.tokengetter
def get_twitter_token(token=None):
    if session.has_key('twitter_token'):
        del session['twitter_token']
    return session.get('twitter_token')


@app.route('/')
def index():
    return render_template('index.html', name = __name__)


#twitter api
@app.route('/login')
def login():
    access_token = session.get('access_token')
    if access_token is None:
        return twitter.authorize(callback=url_for('oauth_authorized',
        next=request.args.get('next') or request.referrer or None))
 
    access_token = access_token[0]
    return redirect('/tweet')
 
 #twitter api
@app.route('/logout')
def logout():
    session.pop('screen_name', None)
    flash('You were signed out')
    return redirect(request.referrer or url_for('index'))
 
@app.route('/tweet')
def tweet():
    status = api.update_status('This is another extra test message for #hacktx')
    return redirect('/')

@app.route('/gettweets')
def get_tweets():
    public_tweets = api.home_timeline()
    for tweet in public_tweets:
        
        while (count < 5):
            print tweet
    return redirect('/')
 
@app.route('/oauth-authorized')
@twitter.authorized_handler
def oauth_authorized(resp):
    next_url = request.args.get('next') or url_for('index')
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)
 
    access_token = resp['oauth_token']
    session['access_token'] = access_token
    session['screen_name'] = resp['screen_name']
 
    session['twitter_token'] = (
        resp['oauth_token'],
        resp['oauth_token_secret']
    )
    
    return redirect(url_for('index'))

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



# Create a list of registered numbers that can call
callers = {
	"+12145347832": "Austin",
	"+18325170044": "Zhifan"
}

# @app.route("/", methods = ["GET", "POST"])
# def respond_to_user():
# 	"""
# 	Respond to a text message using the sender's name.
# 	"""
# 	# Get the number of the user who texted me
# 	from_num = request.values.get("From", None)
# 	if from_num in callers:
# 		return_mess = callers[from_num] + ", thanks for texting me!"
# 	else:
# 		return_mess = "I don't know who you are, but thanks for the text!"
	
# 	# Send them their message back.
# 	return_mess += "\n\n"
# 	return_mess += "This is what you texted me: \n"
# 	body = request.values.get("Body", None)
# 	if body != None:
# 		return_mess += body
# 	else:
# 		return_mess += "You sent nothing :("
# 	resp = twiml.Response()
# 	resp.message(return_mess)
# 	return str(resp)

if __name__ == "__main__":
    app.run()

