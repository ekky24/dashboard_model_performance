from flask import Flask, render_template, url_for, request, jsonify, session
from flask.globals import current_app
from numpy.lib.type_check import real
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
import simplejson
import datetime

from utils.data_connector import set_conn, get_tag_sensor_mapping, get_realtime_data, \
	get_future_prediction_fn, get_anomaly_fn, get_survival_data, close_conn
from credentials.db_credentials import DB_UNIT_MAPPER
from utils.data_cleaner import handle_nan_in_sensor_df, outlier_calculator
import config
import os
import glob
import sys

debug_mode = True

app = Flask(__name__, static_folder="statics")
app.secret_key = 'dashboard_model_performance'

@app.route('/')
def home():
	return render_template('index.html')

@app.route('/anomaly_detection')
def anomaly_detection():
	return render_template('anomaly-detection.html')

@app.route('/future_prediction')
def future_prediction():
	return render_template('future-prediction.html')

@app.route('/survival_analysis')
def survival_analysis():
	return render_template('survival-analysis.html')

@app.route('/get_sensor_mapping')
def get_sensor_mapping():
	resp = {'status': 'failed','data': 'none'}

	try:
		equipment_mapping_files = glob.glob(f'{config.TEMP_FOLDER}/*.csv')

		if not session.get('is_load_equipment_mapping'):
			for f in equipment_mapping_files:
				os.remove(f)
			equipment_mapping_files = []
		
		if len(equipment_mapping_files) > 0:
			equipment_mapping_df = pd.read_csv(f'{equipment_mapping_files[0]}')
		else:
			engine = set_conn('DB_SOKET')
			equipment_mapping_df = get_tag_sensor_mapping(engine)
			close_conn(engine)

			curr_timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')
			equipment_mapping_df.dropna(inplace=True)
			equipment_mapping_df.to_csv(f'{config.TEMP_FOLDER}/equipment_mapping_{curr_timestamp}.csv', \
				index=False)

		resp['status'] = 'success'
		resp['data'] = equipment_mapping_df.to_dict(orient='split')
		session['is_load_equipment_mapping'] = True

	except Exception as e:
		resp['status'] = 'failed'
		resp['data'] = str(e)
		print(f'{str(e)} on line {sys.exc_info()[-1].tb_lineno}')

	return jsonify(resp)

@app.route('/get_raw_data')
def get_raw_data():
	resp = {'status': 'failed','data': 'none'}

	try:
		req_data = dict(request.values)
		unit = req_data['unit']
		tag_name = req_data['tag']
		date_range = req_data['date_range']

		raw_start_date = date_range.split(' - ')[0]
		raw_start_date = raw_start_date.split('/')
		start_date = f'{raw_start_date[2]}-{raw_start_date[1]}-{raw_start_date[0]}'
		start_time = f'{start_date} 00:00:00'

		raw_end_date = date_range.split(' - ')[1]
		raw_end_date = raw_end_date.split('/')
		end_date = f'{raw_end_date[2]}-{raw_end_date[1]}-{raw_end_date[0]}'

		curr_timestamp = datetime.datetime.now()
		curr_date = curr_timestamp.strftime('%Y-%m-%d')

		if end_date == curr_date:
			curr_hour = curr_timestamp.strftime('%H:%M:%S')
			end_time = f'{end_date} {curr_hour}'
		else:
			end_time = f'{end_date} 23:59:59'

		engine = set_conn(unit)
		realtime_df = get_realtime_data(engine, tag_name, start_date, \
			end_date, config.RAW_DATA_RESAMPLE_MIN)
		close_conn(engine)

		dates_set = set(realtime_df.index)
		all_dates = pd.Series(data=pd.date_range(start=start_time, end=end_time, \
			freq=f'{config.RAW_DATA_RESAMPLE_MIN}min'))
		mask = all_dates.isin(realtime_df.index)

		if all_dates[~mask].shape[0] > 0:
			all_data = np.empty((all_dates.shape[0], realtime_df.shape[1]))

			all_data[:] = np.nan
			for i in range(all_dates.shape[0]):
				date = all_dates[i]

				if date in dates_set:
					all_data[i, :] = realtime_df.loc[date].values

			realtime_df = pd.DataFrame(all_data, columns=realtime_df.columns, index=all_dates)

		n_all_data = realtime_df.shape[0]
		n_null = int(realtime_df.isna().sum().values[0])
		outlier_df, n_outlier = outlier_calculator(realtime_df, config.OUTLIER_SIGMA)

		n_outlier = n_outlier[realtime_df.columns[0]]

		stat_desc_mean = float(round(realtime_df.mean(axis=0).values[0], 3))
		stat_desc_std_dev = float(round(realtime_df.std(axis=0).values[0], 3))
		stat_desc_q1 = float(round(realtime_df.quantile(0.25, axis=0).values[0], 3))
		stat_desc_median = float(round(realtime_df.median(axis=0).values[0], 3))
		stat_desc_q3 = float(round(realtime_df.quantile(0.75, axis=0).values[0], 3))
		stat_desc_min = float(round(realtime_df.min(axis=0).values[0], 3))
		stat_desc_max = float(round(realtime_df.max(axis=0).values[0], 3))

		resp['status'] = 'success'
		resp['data'] = {}
			
		resp['data']['realtime'] = {}
		resp['data']['realtime']['data'] = simplejson.dumps(realtime_df.to_dict(orient='split'), \
			ignore_nan=True, default=datetime.datetime.isoformat)
		resp['data']['realtime']['outlier'] = simplejson.dumps(outlier_df.to_dict(orient='split'), \
			ignore_nan=True, default=datetime.datetime.isoformat)
		resp['data']['realtime']['n_normal'] = (n_all_data - n_null - n_outlier) / n_all_data
		resp['data']['realtime']['n_null'] = n_null / n_all_data
		resp['data']['realtime']['n_outlier'] = n_outlier / n_all_data

		resp['data']['stat_desc'] = {}
		resp['data']['stat_desc']['mean'] = stat_desc_mean
		resp['data']['stat_desc']['std_dev'] = stat_desc_std_dev
		resp['data']['stat_desc']['q1'] = stat_desc_q1
		resp['data']['stat_desc']['median'] = stat_desc_median
		resp['data']['stat_desc']['q3'] = stat_desc_q3
		resp['data']['stat_desc']['minimum'] = stat_desc_min
		resp['data']['stat_desc']['maximum'] = stat_desc_max

	except Exception as e:
		resp['status'] = 'failed'
		resp['data'] = str(e)
		print(f'{str(e)} on line {sys.exc_info()[-1].tb_lineno}')

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
		start_time = f'{start_date} 00:00:00'

		raw_end_date = date_range.split(' - ')[1]
		raw_end_date = raw_end_date.split('/')
		end_date = f'{raw_end_date[2]}-{raw_end_date[1]}-{raw_end_date[0]}'

		curr_timestamp = datetime.datetime.now()
		curr_date = curr_timestamp.strftime('%Y-%m-%d')

		if end_date == curr_date:
			curr_hour = curr_timestamp.strftime('%H:%M:%S')
			end_time = f'{end_date} {curr_hour}'
		else:
			end_time = f'{end_date} 23:59:59'

		engine = set_conn(unit)
		realtime_df = get_realtime_data(engine, tag_name, start_date, end_date, config.ANOMALY_RESAMPLE_MIN)
		autoencoder_df, lower_limit_df, upper_limit_df = get_anomaly_fn(engine, \
			tag_name, start_date, end_date, config.ANOMALY_RESAMPLE_MIN)
		close_conn(engine)

		realtime_df = handle_nan_in_sensor_df(realtime_df, config.ANOMALY_RESAMPLE_MIN, start_time, \
			pd.Timestamp(end_time).round(f'{config.ANOMALY_RESAMPLE_MIN}min'))
		autoencoder_df = handle_nan_in_sensor_df(autoencoder_df, config.ANOMALY_RESAMPLE_MIN, \
			start_time, pd.Timestamp(end_time).round(f'{config.ANOMALY_RESAMPLE_MIN}min'))
		lower_limit_df = handle_nan_in_sensor_df(lower_limit_df, config.ANOMALY_RESAMPLE_MIN, \
			start_time, pd.Timestamp(end_time).round(f'{config.ANOMALY_RESAMPLE_MIN}min'))
		upper_limit_df = handle_nan_in_sensor_df(upper_limit_df, config.ANOMALY_RESAMPLE_MIN, \
			start_time, pd.Timestamp(end_time).round(f'{config.ANOMALY_RESAMPLE_MIN}min'))

		ovr_loss = mean_absolute_error(realtime_df.values, autoencoder_df.values)
		ovr_loss = round(ovr_loss, 3)

		metrics_timestamp = pd.date_range(start=start_time, \
			end=pd.Timestamp(end_time).round('1H'), freq=f'1H')

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
		print(f'{str(e)} on line {sys.exc_info()[-1].tb_lineno}')

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
		start_time = f'{start_date} 00:00:00'

		raw_end_date = date_range.split(' - ')[1]
		raw_end_date = raw_end_date.split('/')
		end_date = f'{raw_end_date[2]}-{raw_end_date[1]}-{raw_end_date[0]}'

		curr_timestamp = datetime.datetime.now()
		curr_date = curr_timestamp.strftime('%Y-%m-%d')

		if end_date == curr_date:
			curr_hour = curr_timestamp.strftime('%H:%M:%S')
			end_time = f'{end_date} {curr_hour}'
		else:
			end_time = f'{end_date} 23:59:59'
		
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

		realtime_df = handle_nan_in_sensor_df(realtime_df, config.FUTURE_PREDICTION_RESAMPLE_MIN, start_time, \
			pd.Timestamp(end_time).round(f'{config.FUTURE_PREDICTION_RESAMPLE_MIN}min'))

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

		if prediction_date.empty:
			raise Exception("Insufficient data. Please select a larger date range.")
			
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
		print(f'{str(e)} on line {sys.exc_info()[-1].tb_lineno}')

	return jsonify(resp)

@app.route('/get_survival_analysis_data')
def get_survival_analysis_data():
	resp = {'status': 'failed','data': 'none'}

	try:
		req_data = dict(request.values)
		unit = req_data['unit']
		equipment = req_data['equipment']

		engine = set_conn(unit)
		survival_df = get_survival_data(engine, equipment, config.SURVIVAL_N_PREDICTION)
		close_conn(engine)

		prediction_dict = {
			'timestamp': [],
			'value': [],
		}

		for i in range(config.SURVIVAL_N_PREDICTION):
			curr_row = survival_df.iloc[i]
			curr_idx = survival_df.index[i]
			prediction_dict['timestamp'].append(curr_idx)
			prediction_dict['value'].append(curr_row['f_value'])

		prediction_df = pd.DataFrame(prediction_dict)
		prediction_df.set_index('timestamp', inplace=True)
		
		resp['status'] = 'success'
		resp['data'] = {}
		
		resp['data']['prediction'] = {}
		resp['data']['prediction']['data'] = prediction_df.to_dict(orient='split')
		resp['data']['prediction']['equipment_name'] = equipment

	except Exception as e:
		resp['status'] = 'failed'
		resp['data'] = str(e)
		print(f'{str(e)} on line {sys.exc_info()[-1].tb_lineno}')

	return jsonify(resp)

if __name__ == '__main__':
	if debug_mode:
		app.run(debug=True, port=8000)
	else:
		app.run(host='0.0.0.0', port=5003, debug=True)
	