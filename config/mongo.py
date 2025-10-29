# backend/config/mongo.py
from flask_pymongo import PyMongo
from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()

mongo = PyMongo()

def init_db(app: Flask):
    app.config["MONGO_URI"] = os.getenv("MONGODB_URI")
    mongo.init_app(app)

    # ✅ Attach DB to app context for easy access
    app.db = mongo.db

    print("✅ MongoDB initialized via Flask-PyMongo")
