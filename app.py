from flask import Flask, render_template, url_for, request, jsonify
import pandas as pd
import numpy as np

from utils.data_connector import set_conn, get_tag_sensor_mapping, close_conn
import credentials.db_credentials

app = Flask(__name__, static_folder="statics")

@app.route('/')
def home():
	return render_template('index.html')

@app.route('/anomaly_detection')
def anomaly_detection():
	return render_template('anomaly-detection.html')

@app.route('/get_sensor_mapping')
def get_sensor_mapping():
	resp = {'status': 'failed','data': 'none'}

	try:
		engine = set_conn('DB_SOKET')
		equipment_mapping_df = get_tag_sensor_mapping(engine)

		resp['status'] = 'success'
		resp['data'] = equipment_mapping_df.to_dict(orient='split')

	except Exception as e:
		resp['status'] = 'failed'
		resp['data'] = str(e)

	return jsonify(resp)

if __name__ == '__main__':
	app.run(debug=True, port=8000)