from flask import Flask, render_template, url_for, request, jsonify
from numpy.lib.type_check import real
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, mean_absolute_percentage_error

from utils.data_connector import set_conn, get_tag_sensor_mapping, get_realtime_data, \
	get_future_prediction_fn, get_anomaly_fn, close_conn
from credentials.db_credentials import DB_UNIT_MAPPER
from utils.data_cleaner import handle_nan_in_sensor_df
import config

app = Flask(__name__, static_folder="statics")

@app.route('/')
def home():
	return render_template('index.html')

@app.route('/anomaly_detection')
def anomaly_detection():
	return render_template('anomaly-detection.html')

@app.route('/future_prediction')
def future_prediction():
	return render_template('future-prediction.html')

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
		realtime_df = get_realtime_data(engine, tag_name, start_date, end_date, config.ANOMALY_RESAMPLE_MIN)
		autoencoder_df, lower_limit_df, upper_limit_df = get_anomaly_fn(engine, \
			tag_name, start_date, end_date, config.ANOMALY_RESAMPLE_MIN)
		close_conn(engine)

		ovr_loss = mean_absolute_error(realtime_df.values, autoencoder_df.values)
		ovr_loss = round(ovr_loss, 3)

		metrics_timestamp = pd.date_range(start=start_date, \
			end=pd.Timestamp.now().round('1H'), freq=f'1H')

		metrics_data = []
		metrics_index = []
		for idx, row in enumerate(metrics_timestamp):
			if idx < len(metrics_timestamp)-1:
				curr_realtime = realtime_df.loc[metrics_timestamp[idx]:metrics_timestamp[idx+1]]
				curr_autoencoder = autoencoder_df.loc[metrics_timestamp[idx]:metrics_timestamp[idx+1]]
				metrics_data.append(mean_absolute_error(curr_realtime, curr_autoencoder))
				metrics_index.append(row.strftime('%d/%m/%Y %H:%M:%S'))

		resp['status'] = 'success'
		resp['data'] = {}
		
		resp['data']['realtime'] = realtime_df.to_dict(orient='split')
		resp['data']['autoencoder'] = autoencoder_df.to_dict(orient='split')
		resp['data']['lower_limit'] = lower_limit_df.to_dict(orient='split')
		resp['data']['upper_limit'] = upper_limit_df.to_dict(orient='split')

		resp['data']['metrics'] = {}
		resp['data']['metrics']['index'] = metrics_index
		resp['data']['metrics']['data'] = metrics_data
		resp['data']['metrics']['ovr_loss'] = ovr_loss

	except Exception as e:
		resp['status'] = 'failed'
		resp['data'] = str(e)

	return jsonify(resp)

@app.route('/get_future_prediction_data')
def get_future_prediction_data():
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

		
		###############################################################################
		'''
		SINCE THE PREDICTION DATA HISTORY IS NOT STORE INTO DATABASE, WE PROVIDE MANUAL 
		PREDICTION
		'''
		###############################################################################
		

		engine = set_conn(unit)
		realtime_df = get_realtime_data(engine, tag_name, start_date, \
			end_date, config.FUTURE_PREDICTION_RESAMPLE_MIN)
		# prediction_df = get_future_prediction_fn(engine, tag_name, start_date, \
		# 	end_date, config.FUTURE_PREDICTION_RESAMPLE_MIN)
		close_conn(engine)

		metrics_data = []
		metrics_index = []
		prediction_dict = {
			'timestamp': [],
			'actual': [],
			'prediction': [],
		}

		prediction_date = realtime_df.index[config.FUTURE_PREDICTION_INPUT_STEP:]
		prediction_date = prediction_date[:-config.FUTURE_PREDICTION_OUTPUT_STEP]
		input_step = config.FUTURE_PREDICTION_INPUT_STEP
		output_step = config.FUTURE_PREDICTION_OUTPUT_STEP

		for idx in range(input_step, input_step + len(prediction_date)):
			input_data = realtime_df.iloc[(idx - input_step):idx]
			pred_data = input_data.ewm(alpha=config.FUTURE_PREDICTION_ALPHA, adjust=False).mean().values
			pred_data = pred_data[-output_step:]

			prediction_dict['timestamp'] = realtime_df.index[(idx - input_step):(idx + output_step)]
			prediction_dict['actual'] = realtime_df.iloc[(idx - input_step):(idx + output_step), 0]
			prediction_dict['prediction'] = input_data.values[:, 0].tolist()
			prediction_dict['prediction'] += pred_data[:, 0].tolist()
			
			y_true = realtime_df.iloc[idx:(idx + output_step)].values
			y_pred = pred_data
			metrics_data.append(mean_absolute_percentage_error(y_true, y_pred))
			metrics_index.append(realtime_df.index[idx])

		prediction_df = pd.DataFrame(prediction_dict)
		prediction_df.set_index('timestamp', inplace=True)

		ovr_loss = np.mean(metrics_data)
		ovr_loss = round(ovr_loss, 3)
		
		###############################################################################
		
		resp['status'] = 'success'
		resp['data'] = {}
		
		resp['data']['prediction'] = {}
		resp['data']['prediction']['data'] = prediction_df.to_dict(orient='split')
		resp['data']['prediction']['input_step'] = config.FUTURE_PREDICTION_INPUT_STEP
		resp['data']['prediction']['tag_name'] = realtime_df.columns[0]

		resp['data']['metrics'] = {}
		resp['data']['metrics']['index'] = metrics_index
		resp['data']['metrics']['data'] = metrics_data
		resp['data']['metrics']['ovr_loss'] = ovr_loss

	except Exception as e:
		resp['status'] = 'failed'
		resp['data'] = str(e)

	return jsonify(resp)

if __name__ == '__main__':
	app.run(debug=True, port=8000)