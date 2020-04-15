import re
import os
import string
import random
import hashlib
import datetime
import gunicorn
from urllib.parse import unquote
from pymongo import MongoClient
from flask import render_template
from flask import Flask,redirect,request

app = Flask('app')

client = MongoClient("replace_your_mogo_server")
db = client['hash_table']    #Your mongo table name
posts = db.posts

def validate_url(data):
    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', data['url'])
    if not urls:
        return False
    else:
        return data

def short_code(size=4,chars=string.ascii_uppercase + string.digits+string.ascii_lowercase):
    return ''.join(random.choice(chars) for x in range(size))  

def md5_url(url):
    return hashlib.md5(url.encode('utf-8')).hexdigest()

def hash_to_dict(md5,data):
    hash_dict=dict()
    code=short_code()
    hash_dict={"hash":md5,"url":data['url'],"code":str(code),"timestamp":data['timestamp']}
    return hash_dict

def checker(data):
    md5=md5_url(data['url'])
    query = { "hash": md5 }
    try:
        doc = posts.find_one(query)
        #print("Yah...It's already in db.")
        return "https://u-l.herokuapp.com/"+doc["code"]
    except:
        print("Not in DB. Adding Now......")
        hash_dict=hash_to_dict(md5,data)
        result = posts.insert_one(hash_dict)
        #print('Post ID: {0}'.format(result.inserted_id))
        #print("Added.")
        doc = posts.find_one(query)
        return "https://u-l.herokuapp.com/"+doc['code']

#Flask app starts here
@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(error):
    app.logger.error('Server Error: %s', (error))
    return render_template('404.html'), 500

@app.errorhandler(Exception)
def unhandled_exception(e):
    app.logger.error('Unhandled Exception: %s', (e))
    return render_template('404.html'), 500

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/",methods=['GET','POST'])
def home_post():
    url = unquote(str(request.form['url']))
    timestamp = str(request.form['timestamp'])
    data={"url":url,"timestamp":timestamp}
    short_link = checker(validate_url(data))
    return render_template('index.html',link=short_link,title="Short Link")

@app.route("/<short_code>")
def reroute(short_code):
    query = { "code": short_code }
    doc = posts.find_one(query)
    return redirect(doc['url'], code=302)


#Entry point of the app
if __name__ == '__main__':
    app.run(debug=True)




