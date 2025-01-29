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
from getenergyoutput import *
import datetime

app = Flask(__name__)
@app.route('/')
def home():

    return render_template("index.html", template_folder="templates")

@app.route('/save-coordinates', methods=['POST'])
def save_coordinates():
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if latitude is not None and longitude is not None:
        print(f"Received coordinates: Latitude={latitude}, Longitude={longitude}")
        return_string = main(latitude, longitude)
        
        return jsonify({
            "message": "Coordinates received successfully!",
            "latitude": latitude,
            "longitude": longitude,
            "output": return_string
        })
    else:
        return jsonify({"error": "Invalid data"}), 400


app.debug = True
if (__name__ == "__main__"):
    app.run()