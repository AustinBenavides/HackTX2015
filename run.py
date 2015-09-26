from flask import Flask, request, redirect
import twilio.twiml as twiml

# Init the app as a Flask web server
app = Flask(__name__)

# Create a list of registered numbers that can call
callers = {
	"+12145347832": "Austin",
	"+18325170044": "Zhifan"
}

@app.route("/", methods = ["GET", "POST"])
def respond_to_user():
	"""
	Respond to a text message using the sender's name.
	"""
	# Get the number of the user who texted me
	from_num = request.values.get("From", None)
	if from_num in callers:
		return_mess = callers[from_num] + ", thanks for texting me!"
	else:
		return_mess = "I don't know who you are, but thanks for the text!"
	
	# Send them their message back.
	return_mess += "\n\n"
	return_mess += "This is what you texted me: \n"
	body = request.values.get("Body", None)
	if body != None:
		return_mess += body
	else:
		return_mess += "You sent nothing :("
	resp = twiml.Response()
	resp.message(return_mess)
	return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
