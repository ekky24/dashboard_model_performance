from flask import Flask, render_template, url_for, request, jsonify, session, send_file
from flask.globals import current_app
from numpy.lib.type_check import real
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
import simplejson
import datetime
import pytz
from cachetools import cached, TTLCache
import json

from utils.data_connector import set_conn, get_tag_sensor_mapping, get_realtime_data, \
	get_future_prediction_fn, get_anomaly_fn, get_survival_data, get_anomaly_interval_data, \
	get_sensor_information_from_unit, get_tag_alarm, close_conn
from utils.anomaly_predictor import calculate_limits, get_historian_data, get_model, \
	create_lstm_sequence, flatten_to_2d, detect_anomalies
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

@app.route('/sensor_mapping')
def sensor_mapping():
	return render_template('sensor_mapping.html')

@app.route('/anomaly_detection')
def anomaly_detection():
	return render_template('anomaly-detection.html')

@app.route('/future_prediction')
def future_prediction():
	return render_template('future-prediction.html')

@app.route('/survival_analysis')
def survival_analysis():
	return render_template('survival-analysis.html')

@app.route('/anomaly_validation')
def anomaly_validation():
	return render_template('anomaly-detection-validation.html')

@app.route('/anomaly_detection_bad_model')
def anomaly_detection_bad_model():
	return render_template('anomaly-detection-bad-model.html')

def read_sensor_mapping():
	equipment_mapping_files = glob.glob(f'{config.TEMP_FOLDER}/*.csv')
	equipment_mapping_df = pd.read_csv(f'{equipment_mapping_files[0]}')
	equipment_mapping_df.dropna(inplace=True)

	return equipment_mapping_df

def get_modeled_tags():
	modeled_tags_df = pd.DataFrame()
	soks = os.listdir(f'{config.DATA_FOLDER}/modeled_tags')
	for sok in soks:
		temp_modeled_tags_file = glob.glob(f'{config.DATA_FOLDER}/modeled_tags/{sok}/*.csv')
		temp_modeled_tags_df = pd.read_csv(f'{temp_modeled_tags_file[0]}')
		modeled_tags_df = pd.concat([modeled_tags_df, temp_modeled_tags_df], axis=0)
	
	return modeled_tags_df

@app.route('/get_sensor_mapping')
def get_sensor_mapping():
	resp = {'status': 'failed','data': 'none'}

	try:
		req_data = dict(request.values)
		is_update = req_data['is_update']
		is_update = True if is_update == 'true' else False

		equipment_mapping_files = glob.glob(f'{config.TEMP_FOLDER}/*.csv')
		if len(equipment_mapping_files) > 0 and not is_update:
			equipment_mapping_df = read_sensor_mapping()
		else:
			engine = set_conn('DB_SOKET')
			equipment_mapping_df = get_tag_sensor_mapping(engine)
			close_conn(engine)

			modeled_tags_df = get_modeled_tags()
			
			is_modeled = []
			for idx, row in equipment_mapping_df.iterrows():
				if row['f_tag_name'] in modeled_tags_df['Tag Name'].values.tolist():
					is_modeled.append(True)
				else:
					is_modeled.append(False)

			equipment_mapping_df['is_modeled'] = is_modeled
			
			curr_timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')
			equipment_mapping_df.dropna(inplace=True)
			equipment_mapping_df.to_csv(f'{config.TEMP_FOLDER}/equipment_mapping_{curr_timestamp}.csv', \
				index=False)

		resp['status'] = 'success'
		resp['data'] = equipment_mapping_df.to_dict(orient='split')

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

		engine = set_conn(config.UNIT_NAME_MAPPER[unit])
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
		outlier_df, n_outlier = \
			outlier_calculator(realtime_df, config.OUTLIER_SIGMA)

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

		curr_timestamp = datetime.datetime.now(pytz.timezone(config.TIMEZONE_MAPPER[unit]))
		curr_date = curr_timestamp.strftime('%Y-%m-%d')

		if end_date == curr_date:
			curr_hour = curr_timestamp.strftime('%H:%M:%S')
			end_time = f'{end_date} {curr_hour}'
		else:
			end_time = f'{end_date} 23:59:59'

		engine = set_conn(config.UNIT_NAME_MAPPER[unit])
		engine_soket = set_conn('DB_SOKET')
		realtime_df = get_realtime_data(engine, tag_name, start_date, end_date, config.ANOMALY_RESAMPLE_MIN)
		autoencoder_df, lower_limit_df, upper_limit_df = get_anomaly_fn(engine, \
			tag_name, start_date, end_date, config.ANOMALY_RESAMPLE_MIN)
		l1_alarm, h1_alarm, tag_desc = get_tag_alarm(engine_soket, tag_name)
		close_conn(engine)
		close_conn(engine_soket)

		realtime_df = handle_nan_in_sensor_df(realtime_df, config.ANOMALY_RESAMPLE_MIN, start_time, \
			pd.Timestamp(end_time).round(f'{config.ANOMALY_RESAMPLE_MIN}min'))
		autoencoder_df = handle_nan_in_sensor_df(autoencoder_df, config.ANOMALY_RESAMPLE_MIN, \
			start_time, pd.Timestamp(end_time).round(f'{config.ANOMALY_RESAMPLE_MIN}min'))
		lower_limit_df = handle_nan_in_sensor_df(lower_limit_df, config.ANOMALY_RESAMPLE_MIN, \
			start_time, pd.Timestamp(end_time).round(f'{config.ANOMALY_RESAMPLE_MIN}min'))
		upper_limit_df = handle_nan_in_sensor_df(upper_limit_df, config.ANOMALY_RESAMPLE_MIN, \
			start_time, pd.Timestamp(end_time).round(f'{config.ANOMALY_RESAMPLE_MIN}min'))

		anomaly_marker_df = realtime_df.copy()
		anomaly_marker_df[((anomaly_marker_df[tag_name] <= upper_limit_df[tag_name]) & \
			(anomaly_marker_df[tag_name] >= lower_limit_df[tag_name]))] = np.nan

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
				metrics_index.append(row.strftime('%a, %d %b %Y %H:%M:%S'))

		realtime_df.index = realtime_df.index.strftime('%a, %d %b %Y %H:%M:%S')
		autoencoder_df.index = autoencoder_df.index.strftime('%a, %d %b %Y %H:%M:%S')
		lower_limit_df.index = lower_limit_df.index.strftime('%a, %d %b %Y %H:%M:%S')
		upper_limit_df.index = upper_limit_df.index.strftime('%a, %d %b %Y %H:%M:%S')

		resp['status'] = 'success'
		resp['data'] = {}
		
		resp['data']['realtime'] = realtime_df.to_dict(orient='split')
		resp['data']['autoencoder'] = autoencoder_df.to_dict(orient='split')
		resp['data']['lower_limit'] = lower_limit_df.to_dict(orient='split')
		resp['data']['upper_limit'] = upper_limit_df.to_dict(orient='split')
		resp['data']['anomaly_marker'] = anomaly_marker_df.replace(np.nan, 'null').to_dict(orient='split')

		resp['data']['metrics'] = {}
		resp['data']['metrics']['index'] = metrics_index
		resp['data']['metrics']['data'] = metrics_data
		resp['data']['metrics']['ovr_loss'] = ovr_loss

		resp['data']['alarm'] = {}
		resp['data']['alarm']['l1_alarm'] = l1_alarm
		resp['data']['alarm']['h1_alarm'] = h1_alarm

		resp['data']['tag_info'] = {}
		resp['data']['tag_info']['desc'] = tag_desc

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
		

		engine = set_conn(config.UNIT_NAME_MAPPER[unit])
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
			metrics_index.append(realtime_df.index[idx].strftime('%a, %d %b %Y %H:%M:%S'))

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

		engine = set_conn(config.UNIT_NAME_MAPPER[unit])
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

@app.route('/get_anomaly_detection_bad_model_data')
def get_anomaly_detection_bad_model_data():
	resp = {'status': 'failed','data': 'none'}

	try:
		req_data = dict(request.values)
		unit = req_data['unit']
		time_interval = req_data['time_interval']

		if time_interval == 'hour_1':
			time_interval = 1
		elif time_interval == 'hour_3':
			time_interval = 3
		elif time_interval == 'hour_6':
			time_interval = 6
		elif time_interval == 'hour_12':
			time_interval = 12
		elif time_interval == 'hour_24':
			time_interval = 24
		else:
			raise Exception('Time Interval is not correct.')

		end_time = pd.Timestamp.now(tz=config.TIMEZONE_MAPPER[unit]).round('5min')
		start_time = end_time - datetime.timedelta(hours=time_interval)
		left_index = pd.date_range(start=start_time, end=end_time, freq='5min')
		left_df = pd.DataFrame(index=left_index[1:])
		left_df.index = left_df.index.tz_localize(None)

		engine = set_conn(config.UNIT_NAME_MAPPER[unit])
		interval_anomaly_df = get_anomaly_interval_data(engine, time_interval)
		sensor_information_df = get_sensor_information_from_unit(engine, unit)
		sensor_information_df.set_index('f_tag_name', inplace=True)
		close_conn(engine)

		concated_anomaly_count_df = pd.pivot_table(interval_anomaly_df, values='f_status_limit', index='f_timestamp', columns='f_tag_name')
		concated_anomaly_count_df = pd.merge(left_df, concated_anomaly_count_df, how='left', left_index=True, right_index=True)
		# concated_anomaly_count_df.fillna(1, inplace=True)
		concated_anomaly_count_df.replace([1.0, 2.0], 1.0, inplace=True)

		concated_autoencoder_df = pd.pivot_table(interval_anomaly_df, values='f_value', index='f_timestamp', columns='f_tag_name')
		concated_autoencoder_df = pd.merge(left_df, concated_autoencoder_df, how='left', left_index=True, right_index=True)
		concated_autoencoder_df.interpolate(inplace=True)

		alarm_dict = {
			'tagname': [],
			'h1_alarm': [],
			'l1_alarm': [],
		}
		
		# Rule 1: Get Anomaly Count
		result_anomaly_count_df = concated_anomaly_count_df.sum(axis=0)
		threshold_count = int(0.4 * len(left_df))

		# Rule 2: H1 Alarm Checking and Rule 3: L1 Alarm Checking
		result_h1_df = pd.Series()
		result_l1_df = pd.Series()

		for col in concated_autoencoder_df.columns:
			try:
				curr_h1 = sensor_information_df.loc[[col]].iloc[0]['f_h1_alarm']
				curr_l1 = sensor_information_df.loc[[col]].iloc[0]['f_l1_alarm']
			except KeyError:
				curr_h1 = None
				curr_l1 = None

			curr_h1_df = concated_autoencoder_df[concated_autoencoder_df[col] > curr_h1]
			result_h1_df[col] = len(curr_h1_df)

			curr_l1_df = concated_autoencoder_df[concated_autoencoder_df[col] < curr_l1]
			result_l1_df[col] = len(curr_l1_df)

			alarm_dict['tagname'].append(col)
			alarm_dict['h1_alarm'].append(curr_h1)
			alarm_dict['l1_alarm'].append(curr_l1)

		result_dict = {
			'system': [],
			'equipment': [],
			'tagname': [],
			'anomaly_count': [],
			'h1_alarm_count': [],
			'l1_alarm_count': [],
		}
		for col in list(result_anomaly_count_df.keys()):
			try:
				curr_df = sensor_information_df.loc[[col]]
			except KeyError:
				continue

			result_dict['system'].append(curr_df.iloc[0]['f_system'])
			result_dict['equipment'].append(curr_df.iloc[0]['f_equipment'])
			result_dict['tagname'].append(col)
			result_dict['anomaly_count'].append(result_anomaly_count_df[col])
			result_dict['h1_alarm_count'].append(result_h1_df[col])
			result_dict['l1_alarm_count'].append(result_l1_df[col])

		alarm_df = pd.DataFrame(alarm_dict)
		result_df = pd.DataFrame(result_dict)

		final_result_df = result_df[(result_df['anomaly_count'] >= threshold_count) | 
			(result_df['h1_alarm_count'] >= threshold_count) | (result_df['l1_alarm_count'] >= threshold_count)]

		for f in glob.glob(f"{config.BAD_MODEL_LIST_DUMP_FOLDER}/{unit}*.csv"):
			os.remove(f)
		
		result_filename = f'{unit}.csv'
		final_result_df.to_csv(f'{config.BAD_MODEL_LIST_DUMP_FOLDER}/{result_filename}', index=False)
		
		resp['status'] = 'success'
		resp['data'] = {}

		resp['data']['bad_model_list'] = final_result_df.to_dict(orient='split')
		# resp['data']['alarm_info'] = alarm_df.to_dict(orient='split')

	except Exception as e:
		resp['status'] = 'failed'
		resp['data'] = str(e)
		print(f'{str(e)} on line {sys.exc_info()[-1].tb_lineno}')

	return jsonify(resp)

@app.route('/get_anomaly_detection_validation_data')
def get_anomaly_detection_validation_data():
	resp = {'status': 'failed','data': 'none'}

	try:
		req_data = dict(request.values)
		unit = req_data['unit']
		system = req_data['system']
		equipment = req_data['equipment']
		tags = req_data['tag']
		tags = tags.split(',')
		date_range = req_data['date_range']

		tags = [tag.replace('/','_') for tag in tags]

		raw_start_date = date_range.split(' - ')[0]
		raw_start_date = raw_start_date.split('/')
		start_date = f'{raw_start_date[2]}-{raw_start_date[1]}-{raw_start_date[0]}'

		raw_end_date = date_range.split(' - ')[1]
		raw_end_date = raw_end_date.split('/')
		end_date = f'{raw_end_date[2]}-{raw_end_date[1]}-{raw_end_date[0]}'

		historian_df = get_historian_data(unit, system, equipment, start_date, end_date)
		scaler, sensor_list, models = get_model(unit, system, equipment, tags)
		historian_df = historian_df[sensor_list]
		scaled_historian_data = scaler.transform(historian_df)
		scaled_historian_df = pd.DataFrame(scaled_historian_data, \
			columns=historian_df.columns, index=historian_df.index)
		scaled_historian_df = scaled_historian_df[tags]
		y_preds = np.zeros(historian_df.shape)
		y_preds = y_preds[1:]
		y_preds_df = pd.DataFrame(y_preds, columns=historian_df.columns, \
			index=historian_df.index[1:])

		for idx, tag in enumerate(tags):
			scaled_historian_lstm = create_lstm_sequence(scaled_historian_df[[tag]].values)
			scaled_y_pred = models[tag].predict(scaled_historian_lstm)
			scaled_y_pred = flatten_to_2d(scaled_y_pred)

			y_preds_df.loc[:, tag] = scaled_y_pred[:, 0]
		
		y_preds = scaler.inverse_transform(y_preds_df)
		y_preds_df = pd.DataFrame(y_preds, columns=historian_df.columns, \
			index=historian_df.index[1:])

		historian_df = historian_df[tags]
		y_preds_df = y_preds_df[tags]
			
		diff_shape = np.abs(historian_df.shape[0] - y_preds_df.shape[0])
		historian_df = historian_df.iloc[diff_shape:]		

		LL_df, UL_df = calculate_limits(historian_df, y_preds_df)
		anomaly_lower_df, anomaly_upper_df = detect_anomalies(historian_df, LL_df, UL_df)
		
		resp['status'] = 'success'
		resp['data'] = {}

		resp['data']['realtime'] = historian_df.to_dict(orient='split')
		resp['data']['autoencoder'] = y_preds_df.to_dict(orient='split')
		resp['data']['lower_limit'] = LL_df.to_dict(orient='split')
		resp['data']['upper_limit'] = UL_df.to_dict(orient='split')
		resp['data']['anomaly_lower'] = simplejson.dumps(anomaly_lower_df.to_dict(orient='split'), \
			ignore_nan=True, default=datetime.datetime.isoformat)
		resp['data']['anomaly_upper'] = simplejson.dumps(anomaly_upper_df.to_dict(orient='split'), \
			ignore_nan=True, default=datetime.datetime.isoformat)

		resp['data']['tags'] = tags

	except Exception as e:
		resp['status'] = 'failed'
		resp['data'] = str(e)
		print(f'{str(e)} on line {sys.exc_info()[-1].tb_lineno}')

	return jsonify(resp)

@app.route('/download_anomaly_detection_data', methods=['POST'])
def download_anomaly_detection_data():
	resp = {'status': 'failed','data': 'none'}

	try:
		req_data = dict(request.form)
		req_data = json.loads(req_data['data'])
		curr_date = datetime.datetime.now().strftime('%Y%m%d_%H%M')

		curr_unit = req_data['unit']
		curr_tag_name = req_data['tag_name']
		
		df = pd.DataFrame(req_data)
		df = df.drop(['unit', 'tag_name'], axis=1)
		df['index'] = pd.to_datetime(df['index'])
		df['index'] = df['index'].dt.tz_convert('Asia/Jakarta')
		df['index'] = df['index'].dt.tz_localize(None)

		df.loc[df['anomaly_marker'] == 'null', 'anomaly_marker'] = 'False'
		df.loc[df['anomaly_marker'] != 'False', 'anomaly_marker'] = 'True'
		df.rename(columns={
			'index': 'date',
			'anomaly_marker': 'is_anomaly',
		}, inplace=True)
		
		df.to_csv(f'{config.ANOMALY_DETECTION_DUMP_FOLDER}/download_data.csv', index=False)
	except Exception as e:
		resp['status'] = 'failed'
		resp['data'] = str(e)
		print(f'{str(e)} on line {sys.exc_info()[-1].tb_lineno}')
		return f'{str(e)} on line {sys.exc_info()[-1].tb_lineno}'

	return send_file(f"{config.ANOMALY_DETECTION_DUMP_FOLDER}/download_data.csv",
				mimetype='text/csv',
				attachment_filename=f"{curr_unit}_{curr_tag_name}_{curr_date}_anomaly.csv",
    			as_attachment=True)

if __name__ == '__main__':
	if debug_mode:
		app.run(debug=True, port=8000)
	else:
		app.run(host='0.0.0.0', port=5003, debug=True)
	