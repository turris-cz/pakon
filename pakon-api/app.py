from flask import Flask, jsonify
from backend import fetch_data

app = Flask (__name__)

@app.route('/get')
def get_data():
    return jsonify(fetch_data())