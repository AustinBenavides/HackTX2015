import sys

from flask import Flask, request, redirect, session, render_template
from twilio.rest import TwilioRestClient 
import twilio.twiml

from flask import g, url_for, flash
from flask_oauthlib.client import OAuth

from flask import Flask, request, redirect, url_for, session, g, flash, \
     render_template
from flask_oauth import OAuth

import shelve

import tweepy
from facepy import GraphAPI
import facebook
from hackernews import HackerNews

###Twilio Account Credentials -- specific to Austin's account
TWILIO_NUM = "+14695072796"
ACCOUNT_SID = "ACba6adc0042509e7ced6d2bbbb700b8e6" 
AUTH_TOKEN = "c51fd911c53fde73d78848b3f1bd4ca7" 

###Twitter Credentials -- specific to this app
consumer_key = 'pfN8ThAB7BRVxiLgwdNZGsZgx'
consumer_secret = 'KmoKfwtczF9feghCp9msCHr8lh0U7yfOPwdkuePrsku58yv54b'
oauth = OAuth()
_twitter = oauth.remote_app('twitter',
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

###Facebook Credentials
FACEBOOK_APP_ID = '1632050293739498'
FACEBOOK_APP_SECRET = 'd52df17292bf6cc66fd9f5b7c6370350'
_facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=FACEBOOK_APP_ID,
    consumer_secret=FACEBOOK_APP_SECRET,
    request_token_params={'scope': 'email'}
)


# Load up the database (persistent dictionary)
db = shelve.open("userinfo")

# Create the RESTful web client.
client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN) 

# Initialize Flask server
app = Flask(__name__)
app.config.from_object(__name__)
app.debug = True
app.secret_key = "development key"

@app.route('/')
def index():
    return render_template('index.html', name = __name__)

@app.route('/signup', methods = ['POST'])
def signup():
	# Get the name and the phone number
	name_in = request.cookies.get("name")
	phone_in = "+1" + request.cookies.get("phone")

	print name_in, phone_in

	# Get facebook access info -- DON'T SAVE ANYTHING YET

	# Get twitter access info
	twitter_screen_name = session.get("screen_name")
	twitter_access_token = session.get("access_token")
	twitter_access_token_secret = session.get("access_token_secret")

	# (Over)write the data to the database
	db[phone_in] = {"name": name_in, "screen_name": twitter_screen_name, "access_token": twitter_access_token,
	"access_token_secret": twitter_access_token_secret}

	print "Wrote to database:"
	# print "Db at " + phone_in + " " + db[phone_in]


	hn_bool = True if request.form.get('check_hn')!=None else False
	facebook_bool = True if request.form.get('check_fb')!=None else False
	twitter_bool = True if request.form.get('check_tw')!=None else False


	# Tell the user what he has registered for
	features = ("HACKERNEWS\n" if hn_bool else "") + (" FACEBOOK\n" if facebook_bool else "") + (" TWITTER" if twitter_bool else "")  
	message = client.messages.create(body="Hi " + name_in + ", welcome to Fetch! You enabled the following features:\n" + features + "\n" + "Text MENU to get instructions!",
	to=phone_in,  # Replace with your phone number
	from_=TWILIO_NUM) # Replace with your Twilio number

	return redirect('/')

####################################################################################
######Twitter API ##################################################################
####################################################################################

@_twitter.tokengetter
def get_twitter_token(token = None):
    if session.has_key('twitter_token'):
        del session['twitter_token']
    return session.get('twitter_token')
    
@app.route('/login')
def login():
	# Try to get the access token and access token secret
    access_token = session.get('access_token')
    access_token_secret = session.get('access_token_secret')
    if access_token is None:
        return _twitter.authorize(callback=url_for('oauth_authorized',
        next=request.args.get('next') or request.referrer or None)) 
    return redirect('/')

# @app.route('/logout')
# def logout():
#     session.pop('screen_name', None)
#     flash('You were signed out')
#     return redirect(request.referrer or url_for('index'))
 
@app.route('/oauth-authorized')
@_twitter.authorized_handler
def oauth_authorized(resp):
    next_url = request.args.get('next') or url_for('index')
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)
 
    access_token = resp['oauth_token']
    access_token_secret = resp['oauth_token_secret']
    session['access_token'] = access_token
    session['access_token_secret'] = access_token_secret
    session['screen_name'] = resp['screen_name']
 
    session['twitter_token'] = (
        resp['oauth_token'],
        resp['oauth_token_secret']
    )
    
    return redirect(url_for('index'))

def get_twitter_account_tokens(from_num):
    # See if the number is in the database
    if db.has_key(from_num):
    	# Load up the twitter account info
    	access_token = db[from_num]["access_token"]
    	access_token_secret = db[from_num]["access_token_secret"]
    else:
    	# Load two empty strings
    	access_token = ""
    	access_token_secret = ""
    if (access_token.equals("")) or (access_token_secret.equals("")):
    	raise "No credentials!"
    print "Loaded twitter account info:", access_token, access_token_secret
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    return api

# @app.route('/readTweets')
def read_n_tweets(from_num, num_to_read):
	print "in read_tweets"
	api = get_twitter_account_tokens(from_num)
	tweets = api.home_timeline()
	# Get the requested number of tweets
	print "ok"
	req_tweets = []
	for i in range(num_to_read):
		print "another"
		req_tweets.append(tweets[i])
	return req_tweets

# @app.route("/tweet")
def tweet_text(from_num, tweet_content):
	print "Database information for " + str(from_num) + str(db[from_num])
	api = get_twitter_account_tokens(from_num)
	api.update_status(tweet_content)

####################################################################################
###### Hacker News API #############################################################
####################################################################################

@app.route('/news')
def get_news(from_num, num_headlines):
	hn = HackerNews()
	print "Starting HN"
	news_lst = []
	for story_id in hn.top_stories(limit=num_headlines):
		news_lst.append(hn.get_item(story_id).title + "\n")
	return news_lst
####################################################################################
###### Facebook API #############################################################
####################################################################################

@_facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')


@app.route('/flogin')
def f_login():
    return _facebook.authorize(callback=url_for('facebook_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True))
    # return redirect('/')


@app.route('/login/authorized')
@_facebook.authorized_handler
def facebook_authorized(resp):
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    session['oauth_token'] = (resp['access_token'], '')
    me = _facebook.get('/me')
    # return 'Logged in as id=%s name=%s redirect=%s' % \
    #     (me.data['id'], me.data['name'], request.args.get('next'))
    return redirect('/')

@app.route('/fpost')
def f_post(picture):
    graph = GraphAPI("CAAXMV1IDjZBoBAC0Be3HMvZA0lPPub735gJiSpwSqGmLTZBrZAqTki8tfqKAUUkAeMoKsKTZBT7nxgIj98S2rXdJk0l9UDnRxCyVi9DvSE5lniRBoUrZC7dx5b1NE5gQO3w6VFB1wqwf9G5OGNS56wGyDWHwBAomLDdTJfIWYX6nk6IetNq73ZC9ps9JuCPoOHOAf8vqjR1eAZDZD")
    # print graph.get('me/posts')
    graph.post(
        path = 'me/photos',
        # source = open('test.jpg', 'rb')
        source = picture
    )

####################################################################################

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
    header = "Welcome to Fetch!\n\n"
    question = "What would you like to do?\n"
    op1 = "1) Email(X)\n"
    op2 = "2) Facebook(X)\n"
    op3 = "3) Twitter\n"
    op4 = "4) News\n\n"
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
    session["state"] = "email"

    #Generate the response
    resp = twilio.twiml.Response()
    header = "You picked email!\n\n"
    warning = "This branch is still under construction.\n\n"
    prompt = "Text BACK to go to the previous screen, or text MENU to go to the main menu."
    text = header + warning + prompt
    resp.message(text)

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
    header = "You picked Facebook!\n\n"
    warning = "This branch is still under construction.\n\n"
    prompt = "Text BACK to go to the previous screen, or text MENU to go to the main menu."
    text = header + warning + prompt
    resp.message(text)

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
    question = "How many tweets would you like to read?\n\n"
    prompt = "Text a number (1-25) to receive tweets, BACK to return to the previous menu, or MENU to return to the main menu."
    text = question + prompt
    resp.message(text)

    return resp

def post_tweet():
    """
    Ask the user what they would like to write, and post it.
    """
    # Update the state
    session["state"] = "posttweet"

    # Generate the response
    resp = twilio.twiml.Response()
    header = "What would you like to post?\n\n"
    prompt = prompt = "Text anything (except BACK or MENU) to tweet, BACK to return to the previous options, or MENU to return to the main menu."
    text = header + prompt
    resp.message(text)

    return resp

def handle_twitter_read():
	"""
	Get the number of tweets to read and display that many to the user.
	"""
	# Update the state
	session["state"] = "readingtweets"

	tweet_req = int(request.values.get("Body", None))
	tweet_from_num = request.values.get("From", None)
	if ((tweet_req != None) and (not tweet_req > 25) and (not tweet_req < 1) and (tweet_from_num != None)):
		try:
			# Get the number of tweets
			tweet_lst = read_n_tweets(tweet_from_num, tweet_req)
			# Generate the response
			resp = twilio.twiml.Response()
			resp.message("Here are the tweets you requested from: " + db[tweet_from_num]["screen_name"] + "\n\n")
			for twt in tweet_lst:
				# Convert the tweet's text into ascii
				unicode_twt = twt.text
				tweet_str = unicode_twt.encode("ascii", "ignore")
				# Get the number of favotites
				tweet_str += "\n    Favorites: " + str(twt.favorite_count)
				# Get the number of retweets
				tweet_str += "\n    Retweets: " + str(twt.retweet_count)
				# Create the message
				resp.message(tweet_str)
				print tweet_str
			# Ask the user if they want to do anything else.
			question = "Would you like to read more tweets?\n\n"
			prompt = "Text a number (1-25) to receive tweets, BACK to return to the previous menu, or MENU to return to the main menu."
			text = question + prompt
			resp.message(text)
			return resp
		except "No credentials!" as e:
			# Generate the response
			resp = twilio.twiml.Response()
			resp.message("You are not registered to read tweets. Please update your account information online.")
			return resp
		# except tweepy.TweepError as e:
		# 	print e
		# 	print type(e)
		# 	print e.__dict__
		# 	print e.reason
		# 	print type(e.reason)
		# 	print e.response.status
		# 	print e.message[0]['code']
		# 	print e.args[0][0]['code']
		except:
			print "Unexpected error:", sys.exc_info()[0]
			# Notify user of unsuccessful post
			resp = twilio.twiml.Response()
			header = "Read not successful. Resend previous number to try again.\n\n"
			prompt = "Text BACK to go to previous menu or MENU to go to the main menu."
			text = header + prompt
			resp.message(header)
			return resp
	else:
		# Nothing to post
		resp = twilio.twiml.Response()
		header = "Read not successful. Resend previous number to try again.\n\n"
		prompt = "Text BACK to go to previous menu or MENU to go to the main menu."
		text = header + prompt
		resp.message(header)
		return resp		

def handle_twitter_post():
	"""
	Take the user's input and post it to Twitter.
	"""
	# Update the state
	session["state"] = "postingtweets"

	tweet_text = request.values.get("Body", None)
	tweet_from_num = request.values.get("From", None)
	if (tweet_text != None) and (tweet_from_num != None):
		try:
			# Tweet it!
			tweet_text(tweet_from_num, tweet_text)
			# Confirm the tweet was sent
			resp = twilio.twiml.Response()
			header = "Tweet posted to : " + db[tweet_from_num]["screen_name"] +"\n\n"
			text = header + tweet_text
			resp.message(text)
			# Ask the user if they want to do anything else.
			question = "Would you like to post another tweet?\n\n"
			prompt = "Send a text with anything (but BACK or MENU) to post it to twitter, BACK to return to the previous menu, or MENU to return to the main menu."
			text = question + prompt
			resp.message(text)
			return resp
		except "No credentials!" as e:
			# Generate the response
			resp = twilio.twiml.Response()
			resp.message("You are not registered to send tweets. Please update your account information online.")
			return resp
		# except tweepy.TweepError as e:
		# 	print e
		# 	print type(e)
		# 	print e.__dict__
		# 	print e.reason
		# 	print type(e.reason)
		# 	print e.response.status
		# 	print e.message[0]['code']
		# 	print e.args[0][0]['code']
		except:
			print "Unexpected error:", sys.exc_info()[0]
			# Notify user of unsuccessful post
			resp = twilio.twiml.Response()
			header = "Post not successful. Resend tweet to try again.\n\n"
			prompt = "Text BACK to go to previous menu or MENU to go to the main menu."
			text = header + prompt
			resp.message(header)
			return resp
	else:
		# Nothing to post
		resp = twilio.twiml.Response()
		header = "Post not successful. Resend tweet to try again.\n\n"
		prompt = "Text BACK to go to previous menu or MENU to go to the main menu."
		text = header + prompt
		resp.message(header)
		return resp

def news():
    """
    Display main menu for News.
    """
    # Update the state
    session["state"] = "news"

    #Generate the response
    resp = twilio.twiml.Response()
    header = "You picked News!\n\n"
    question = "What would you like to do?\n"
    op1 = "1) Read news\n\n"
    prompt = "Text the number corresponding to your choice, "
    prompt2 = "BACK to return to the previous menu, or MENU to go to the main menu."
    text = header + question + op1 + prompt + prompt2
    resp.message(text)

    return resp

def handle_news_menu_choice():
    """
    Respond to user's selection of one of the News options.
    """
    # Delegate control based on the user's choice
    choice = request.values.get("Body", None)
    if choice in news_choices:
        return news_choices[choice]()
    else:
        return invalid_choice()

def read_news_page():
    """
    Ask the user how many headlines they want to read, and fetch them.
    """
    # Update the state
    session["state"] = "readnews"

    # Generate the response
    resp = twilio.twiml.Response()
    question = "How many headlines would you like to read?\n\n"
    prompt = "Text a number (1-25) to receive headlines, BACK to return to the previous menu, or MENU to return to the main menu."
    text = question + prompt
    resp.message(text)

    return resp

def handle_news_read():
	"""
	Respond to user's selection for number of headlines to read, and present them.
	"""
	# Update the state
	session["state"] = "readingnews"

	news_req = int(request.values.get("Body", None))
	news_from_num = request.values.get("From", None)
	if ((news_req != None) and (not news_req > 25) and (not news_req < 1) and (news_from_num != None)):
		try:
			print news_from_num, news_req
			# Get the number of tweets
			news_lst = get_news(news_from_num, news_req)
			print "Got news"
			# Generate the response
			resp = twilio.twiml.Response()
			resp.message("Here are the headlines you requested from: HackerNews\n\n")
			for hl in news_lst:
				# Convert the tweet's text into ascii
				hl_str = hl.encode("ascii", "ignore")
				# Create the message
				resp.message(hl_str)
				print hl_str
			# Ask the user if they want to do anything else.
			question = "Would you like to read more news?\n\n"
			prompt = "Text a number (1-25) to receive headlines, BACK to return to the previous menu, or MENU to return to the main menu."
			text = question + prompt
			resp.message(text)
			return resp
		except "No credentials!" as e:
			# Generate the response
			resp = twilio.twiml.Response()
			resp.message("You are not registered to read news. Please update your account information online.")
			return resp
		# except tweepy.TweepError as e:
		# 	print e
		# 	print type(e)
		# 	print e.__dict__
		# 	print e.reason
		# 	print type(e.reason)
		# 	print e.response.status
		# 	print e.message[0]['code']
		# 	print e.args[0][0]['code']
		except:
			print "Unexpected error:", sys.exc_info()[0]
			# Notify user of unsuccessful post
			resp = twilio.twiml.Response()
			header = "Read not successful. Resend previous number to try again.\n\n"
			prompt = "Text BACK to go to previous menu or MENU to go to the main menu."
			text = header + prompt
			resp.message(header)
			return resp
	else:
		# Nothing to post
		resp = twilio.twiml.Response()
		header = "Read not successful. Resend previous number to try again.\n\n"
		prompt = "Text BACK to go to previous menu or MENU to go to the main menu."
		text = header + prompt
		resp.message(header)
		return resp		

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
    "email": email,
    # Facebook
    "facebook": facebook,
    # Twitter
    "twitter": handle_twitter_menu_choice,
    "readtweets": handle_twitter_read,
    "readingtweets": handle_twitter_read,
    "posttweet": handle_twitter_post,
    "postingtweets": handle_twitter_post,
    # News
    "news": handle_news_menu_choice,
    "readnews": handle_news_read,
    "readingnews": handle_news_read
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
    "readingtweets": twitter,
    "posttweet": twitter,
    "postingtweets": twitter,
    # News
    "news": menu,
    "readnews": news,
    "readingnews": news
}

menu_choices = {
    "1": email,
    "2": facebook,
    "3": twitter,
    "4": news
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

news_choices = {
    "1": read_news_page
}

# Run as a script
if __name__ == "__main__":
    app.run(debug=True)


