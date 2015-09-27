
from flask import Flask, request, redirect, session, render_template
from twilio.rest import TwilioRestClient 
import twilio.twiml

from flask import g, url_for, flash
from flask_oauthlib.client import OAuth

from flask import Flask, request, redirect, url_for, session, g, flash, \
     render_template
from flask_oauth import OAuth
 
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

 
# put your own credentials here 
ACCOUNT_SID = "ACba6adc0042509e7ced6d2bbbb700b8e6" 
AUTH_TOKEN = "c51fd911c53fde73d78848b3f1bd4ca7" 
 
client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN) 


# Each session object makes use of a secret key.
app = Flask(__name__)
app.config.from_object(__name__)
app.debug = True
app.secret_key = "development key"
oauth = OAuth()
# app.config.from_pyfile('local_settings.py')
# Use Twitter as example remote application
twitter = oauth.remote_app('twitter',
    # unless absolute urls are used to make requests, this will be added
    # before all URLs.  This is also true for request_token_url and others.
    base_url='https://api.twitter.com/1/',
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
    return session.get('twitter_token')


@app.route('/')
def landingpage():
	#twitter api

	if request.method == 'POST':
		if request.form['submit'] == 'Sign in with Twitter':
			access_token = session.get('access_token')
			if access_token is None:
				return redirect(url_for('login'))
			else:
				access_token = access_token[0]

	return render_template('index.html', name = __name__)

#twitter api
@app.route('/login')
def login():
    return twitter.authorize(callback=url_for('oauth_authorized',
        next=request.args.get('next') or request.referrer or None))
 
 #twitter api
@app.route('/logout')
def logout():
    session.pop('screen_name', None)
    flash('You were signed out')
    return redirect(request.referrer or url_for('index'))
 
 
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

@app.route("/respondtouser", methods = ["GET", "POST"])
def respond_to_user():
	"""
	Reply to the user's message with the appropriate response.
	"""
	# Count the number of times this user has texed us (this session)
	counter = session.get("counter", 0)
	counter += 1
	session["counter"] = counter

	# Get the user's phone number and try to match it to a name
	from_num = request.values.get("From", None)
	is_registered = from_num in callers

	response = ""

	# If counter is zero, present the user with a display of options
	if counter == 0:
		# User has initiated session
		if (is_registered):
			# Present the user with a list of options
			response = str(menu())
		else:
			# Tell the user to register online
			response = str(reject_user())
	else:
		# Get function pointer to the next step
		next = determine_next_prompt()
		# Execute the next step
		response = str(next())

	return response

def determine_next_prompt():
	"""
	Parse the body of the user's text message to determine what to
	do next.
	"""
	# Read the body of the message
	body = request.values.get("Body", None)

	if body in control_cmds:
		# User has entered a control command -- execute
		return control_cmds[body]
	else:
		# Get the user's state and transition to next 
		user_state = session.get("state", None)
		if user_state != None:
			return state_trans[user_state]
		else:
			return invalid_choice

def back():
	"""
	Go back to the previous state and present the relevant info the user.
	"""
	# Revert to the previous state and act on it
	return state_trans_back[session.get("state")]()

def menu():
	"""
	Display the main menu and prompt the user to select a media category.
	"""
	# Update the user's state
	session["state"] = "menu"

	# Define message components
	header = "Welcome to HackTX!\n\n"
	question = "What would you like to do?\n"
	op1 = "1) Email\n"
	op2 = "2) Facebook\n"
	op3 = "3) Twitter\n"
	op4 = "4) Wikipedia\n\n"
	prompt = "Text the number corresponding to your choice."

	# Build the message
	text = header + question + op1 + op2 + op3 + op4 + prompt

	# Create the response and attach the message
	resp = twilio.twiml.Response()
	resp.message(text)

	print "Listing options"

	return resp

def handle_menu_choice():
	"""
	Acts on the reader's choice from the menu.
	"""
	# Delegate control based on the user's choice
	choice = request.values.get("Body", None)
	if choice in menu_choices:
		return menu_choices[choice]()
	else:
		return invalid_choice()

def email():
	"""
	Display main menu for email.
	"""
	# Update the state
	session["state"] = "Email"

	#Generate the response
	resp = twilio.twiml.Response()
	resp.message("You picked email!")

	return resp

def handle_email_menu_choice():
	"""
	Respond to user's selection of one of the email options.
	"""
	# Delegate control based on the user's choice
	choice = request.values.get("Body", None)
	if choice in email_choices:
		return email_choices[choice]()
	else:
		return invalid_choice()

def read_emails():
	pass

def send_email():
	pass

def facebook():
	"""
	Display main menu for Facebook.
	"""
	# Update the state
	session["state"] = "facebook"

	#Generate the response
	resp = twilio.twiml.Response()
	resp.message("You picked Facebook!")

	return resp

def handle_facebook_menu_choice():
	"""
	Respond to user's selection of one of the Facebook options.
	"""
	# Delegate control based on the user's choice
	choice = request.values.get("Body", None)
	if choice in facebook_choices:
		return facebook_choices[choice]()
	else:
		return invalid_choice()

def read_statuses():
	pass

def post_status():
	pass

def twitter():
	"""
	Display main menu for Twitter.
	"""
	# Update the state
	session["state"] = "twitter"

	#Generate the response
	resp = twilio.twiml.Response()
	header = "You picked Twitter!\n\n"
	question = "What would you like to do?\n"
	op1 = "1) Read tweets\n"
	op2 = "2) Post tweet\n\n" 
	prompt = "Text the number corresponding to your choice, or text "
	prompt2 = "BACK to go back, or MENU to go to the main menu."
	text = header + question + op1 + op2 + prompt + prompt2
	resp.message(text)

	return resp

def handle_twitter_menu_choice():
	"""
	Respond to user's selection of one of the Twitter options.
	"""
	# Delegate control based on the user's choice
	choice = request.values.get("Body", None)
	if choice in twitter_choices:
		return twitter_choices[choice]()
	else:
		return invalid_choice()

def read_tweets():
	"""
	Ask the user what number of tweets they would like to read, 
	and present the requested number.
	"""
	# Update the state
	session["state"] = "readtweets"

	# Generate the response
	resp = twilio.twiml.Response()
	resp.message("How many tweets would you like to read?")

	return resp

def post_tweet():
	"""
	Ask the user what they would like to write, and post it.
	"""
	# Update the state
	session["state"] = "posttweet"

	# Generate the response
	resp = twilio.twiml.Response()
	resp.message("What would you like to post?")

	return resp

def wikipedia():
	"""
	Display main menu for Wikipedia.
	"""
	# Update the state
	session["state"] = "wikipedia"

	#Generate the response
	resp = twilio.twiml.Response()
	resp.message("You picked Wikipedia!")

	return resp

def handle_wikipedia_menu_choice():
	"""
	Respond to user's selection of one of the Wikipedia options.
	"""
	# Delegate control based on the user's choice
	choice = request.values.get("Body", None)
	if choice in wikipedia_choices:
		return wikipedia_choices[choice]()
	else:
		return invalid_choice()

def read_wiki_page():
	pass

def reject_user():
	"""
	Tells an unregistered user to register online.
	"""
	# Update the user's state
	session["state"] = "rejected"

	# Tell user to register online.
	header = "You're just one step away from accessing the web over text!\n\n"
	prompt = "Just register at our site (INSERT SITE URL HERE) and we'll take it from there."

	# Build the message
	text = header + prompt

	# Create the response and attach the message
	resp = twilio.twiml.Response()
	resp.message(text)

def handle_rejection():
	"""
	Follows up with the user if they send a text after already
	getting rejected for not being registered.
	"""
	#Generate the response
	resp = twilio.twiml.Response()
	resp.message("Please register on our website (INSERT URL HERE)")

	return resp

def invalid_choice():
	"""
	Tells the user that they selected an invalid option and asks 
	that they pick again. NOTE: does not update state.
	"""
	# Generate the response
	resp = twilio.twiml.Response()
	resp.message("Invalid choice. Please select a valid option.")

	return resp

def mirror_user():
	"""
	Mirror the messages sent from the user.
	"""
	# Count the number of times this user has texed us (this session)
	counter = session.get("counter", 0)
	counter += 1
	session["counter"] = counter

	# Get the number of the user who texted me
	from_num = request.values.get("From", None)

	# Search the user and add their name to the message
	return_mess = ""
	if from_num in callers:
		return_mess += callers[from_num] + ", thanks for texting me!"
	else:
		return_mess += "I don't know who you are, but thanks for the text!"
	
	# Tell user how many times they've texted this session
	return_mess += "\n\nYou have texted us " + str(counter) + " times." 

	# Send them their message back.
	return_mess += "\n\n"
	return_mess += "This is what you texted me: \n"
	body = request.values.get("Body", None)
	if body != None:
		return_mess += body
	else:
		return_mess += "You sent nothing :("

	# Create the response
	resp = twilio.twiml.Response()
	message = resp.message(return_mess)

	# Send them their images back
	num_media = int(request.values.get("NumMedia", None))
	print num_media
	for i in range(num_media):
		message.menu_choices(request.values.get("MediaUrl" + str(i), None))
		continue
	return str(resp)

control_cmds = {
	"MENU": menu,
	"BACK": back,
}

state_trans = {
	"menu": handle_menu_choice,
	"reject": handle_rejection,
	# Email
	"email": handle_email_menu_choice,
	# Facebook
	"facebook": handle_facebook_menu_choice,
	# Twitter
	"twitter": handle_twitter_menu_choice,
	"readtweets": read_tweets,
	"posttweet": post_tweet,
	# Wikipedia
	"wikipedia": handle_wikipedia_menu_choice
}

state_trans_back = {
	"menu": menu,
	"reject": respond_to_user,
	# Email
	"email": menu,
	# Facebook
	"facebook": menu,
	# Twitter
	"twitter": menu,
	"readtweets": twitter,
	"posttweet": twitter,
	# Wikipedia
	"wikipedia": menu
}

menu_choices = {
	"1": email,
	"2": facebook,
	"3": twitter,
	"4": wikipedia
}

email_choices = {
	"1": read_emails,
	"2": send_email
}

facebook_choices = {
	"1": read_statuses,
	"2": post_status
}

twitter_choices = {
	"1": read_tweets,
	"2": post_tweet
}

wikipedia_choices = {
	"1": read_wiki_page
}

# Run as a script
if __name__ == "__main__":
    app.run(debug=True)

