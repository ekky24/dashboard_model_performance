from flask import Flask, render_template, url_for, request, jsonify
import pandas as pd
import numpy as np

from utils.data_connector import set_conn, get_tag_sensor_mapping, get_realtime_data, get_anomaly_data, close_conn
from credentials.db_credentials import DB_UNIT_MAPPER
from utils.data_cleaner import handle_nan_in_sensor_df

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
		close_conn(engine)

		resp['status'] = 'success'
		resp['data'] = equipment_mapping_df.to_dict(orient='split')

	except Exception as e:
		resp['status'] = 'failed'
		resp['data'] = str(e)

	return jsonify(resp)

@app.route('/get_anomaly_detection_data')
def get_anomaly_detection_data():
	resp = {'status': 'failed','data': 'none'}

	try:
		req_data = dict(request.values)
		unit = req_data['unit']
		tag_name = req_data['tag']
		date_range = req_data['date_range']

		raw_start_date = date_range.split(' - ')[0]
		raw_start_date = raw_start_date.split('/')
		start_date = f'{raw_start_date[2]}-{raw_start_date[1]}-{raw_start_date[0]}'

		raw_end_date = date_range.split(' - ')[1]
		raw_end_date = raw_end_date.split('/')
		end_date = f'{raw_end_date[2]}-{raw_end_date[1]}-{raw_end_date[0]}'

		engine = set_conn(unit)
		realtime_df = get_realtime_data(engine, tag_name, start_date, end_date)
		autoencoder_df, lower_limit_df, upper_limit_df = get_anomaly_data(engine, tag_name, start_date, end_date)
		close_conn(engine)

		resp['status'] = 'success'
		resp['data'] = {}
		
		resp['data']['realtime'] = realtime_df.to_dict(orient='split')
		resp['data']['autoencoder'] = autoencoder_df.to_dict(orient='split')
		resp['data']['lower_limit'] = lower_limit_df.to_dict(orient='split')
		resp['data']['upper_limit'] = upper_limit_df.to_dict(orient='split')

	except Exception as e:
		resp['status'] = 'failed'
		resp['data'] = str(e)

	return jsonify(resp)

if __name__ == '__main__':
	app.run(debug=True, port=8000)