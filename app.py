import os
from pathlib import Path
import json
from flask import Flask, request, jsonify, g
from flask_expects_json import expects_json
from flask_cors import CORS
from PIL import Image
from huggingface_hub import Repository
from flask_apscheduler import APScheduler
import shutil
import sqlite3
import subprocess
from jsonschema import ValidationError

MODE = os.environ.get('FLASK_ENV', 'production')
IS_DEV = MODE == 'development'
app = Flask(__name__, static_url_path='/static')
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

CORS(app)

TOKEN = os.environ.get('HUGGING_FACE_HUB_TOKEN')

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    # if not IS_DEV:
    #     print("Starting scheduler -- Running Production")
    #     scheduler = APScheduler()
    #     scheduler.add_job(id='Update Dataset Repository',
    #                       func=update_repository, trigger='interval', hours=1)
    #     scheduler.start()
    # else:
    #     print("Not Starting scheduler -- Running Development")
    app.run(host='0.0.0.0',  port=int(
        os.environ.get('PORT', 7860)), debug=True, use_reloader=IS_DEV)
