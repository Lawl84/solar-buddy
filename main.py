from flask import Flask, redirect, jsonify, render_template, request
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from google.oauth2 import service_account
from googleapiclient.discovery import build
import requests
import openai
import json
import hashlib
import random
from flask_cors import CORS
from bcrypt import hashpw, gensalt, checkpw
import math
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from mailersend import emails

app = Flask(__name__)
@app.route('/')
def home():
    return render_template("index.html", template_folder="templates")

app.debug = True
if (__name__ == "__main__"):
    app.run()