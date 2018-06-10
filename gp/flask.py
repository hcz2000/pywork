from flask import Flask
from flask import request
from flask import make_response

app=Flask(__name__)

@app.route("/")
def index():
    user_agent=request.headers.get('User-Agent')
    return "<h1>Your agent is %s</h1>" % user_agent

@app.route("/cookie")
def cookie():
    response=make_response("<h1>This document carries a cookie!</h1>") 
    response.set_cookie("answer","42")
    return response 

@app.route("/user/<name>")
def user(name):
    return "<h1>Hello %s !</h1>" % name

if __name__=='__main__':
    app.run(debug=True)