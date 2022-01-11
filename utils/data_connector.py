from numpy.lib.type_check import real
import pandas as pd
import numpy as np
import sqlalchemy as db
from credentials.db_credentials import DB_SERVER, DB_LOCAL, DB_UNIT_MAPPER, TB_MAPPER
from utils.data_cleaner import handle_nan_in_sensor_df

def set_conn(unit):
	engine = db.create_engine(f"mysql+mysqlconnector://{DB_SERVER['username']}:{DB_SERVER['password']}@{DB_SERVER['host']}/{DB_UNIT_MAPPER[unit]}",echo=False)
	return engine

def get_tag_sensor_mapping(engine):
	query = "SELECT u.f_unit_name f_unit, e.f_equipment_name_alt1 f_system, e.f_equipment_name f_equipment, \
		t.f_tag_name f_tag_name from db_soket.tb_im_units u INNER JOIN db_soket.tb_im_equipments e \
		ON u.f_unit_id = e.f_unit_id \
		INNER JOIN db_soket.tb_im_tags t ON e.f_equipment_id = t.f_equipment_id"
	result_df = pd.read_sql(query, con=engine)

	return result_df

def get_realtime_data(engine, tag_name, start_date, end_date, resample_min):
	query = f"SELECT f_address_no, f_date_rec, f_value FROM tb_bulk_history WHERE f_address_no = \
		'{tag_name}' AND cast(f_date_rec as date) BETWEEN '{start_date}' AND '{end_date}'"
	realtime_df = pd.read_sql(query, con=engine)

	if realtime_df.empty:
		raise Exception('Data is unavailable.')

	realtime_df["f_value"] = pd.to_numeric(realtime_df["f_value"])
	realtime_df = pd.pivot_table(realtime_df, values='f_value', index='f_date_rec', \
		columns='f_address_no').reset_index()
	realtime_df.set_index('f_date_rec', inplace=True)
	realtime_df.sort_index(ascending=True, inplace=True)
	realtime_df = realtime_df.resample(f'{resample_min}min').mean()

	return realtime_df

def get_anomaly_fn(engine, tag_name, start_date, end_date, resample_min):
	query = f"SELECT f_tag_name, f_timestamp, f_value, f_upper_limit, f_lower_limit FROM \
		tb_rb_anomaly_history WHERE f_tag_name = '{tag_name}' AND cast(f_timestamp as date) \
		BETWEEN '{start_date}' AND '{end_date}'"
	result_df = pd.read_sql(query, con=engine)

	if result_df.empty:
		raise Exception('Data is unavailable.')

	result_df["f_value"] = pd.to_numeric(result_df["f_value"])
	result_df["f_lower_limit"] = pd.to_numeric(result_df["f_lower_limit"])
	result_df["f_upper_limit"] = pd.to_numeric(result_df["f_upper_limit"])

	autoencoder_df = pd.pivot_table(result_df, values='f_value', index='f_timestamp', columns='f_tag_name').reset_index()
	autoencoder_df.set_index('f_timestamp', inplace=True)
	autoencoder_df.sort_index(ascending=True, inplace=True)

	lower_limit_df = pd.pivot_table(result_df, values='f_lower_limit', index='f_timestamp', columns='f_tag_name').reset_index()
	lower_limit_df.set_index('f_timestamp', inplace=True)
	lower_limit_df.sort_index(ascending=True, inplace=True)

	upper_limit_df = pd.pivot_table(result_df, values='f_upper_limit', index='f_timestamp', columns='f_tag_name').reset_index()
	upper_limit_df.set_index('f_timestamp', inplace=True)
	upper_limit_df.sort_index(ascending=True, inplace=True)

	return autoencoder_df, lower_limit_df, upper_limit_df

def get_tag_alarm(engine, tag_name):
	l1_alarm = None
	h1_alarm = None

	query = f"SELECT f_tag_name, f_l1_alarm, f_h1_alarm FROM \
		tb_im_tags WHERE f_tag_name = '{tag_name}'"
	result_df = pd.read_sql(query, con=engine)

	if not result_df.empty:
		l1_alarm = result_df.iloc[0]['f_l1_alarm']
		h1_alarm = result_df.iloc[0]['f_h1_alarm']
	
	return l1_alarm, h1_alarm

def get_future_prediction_fn(engine, tag_name, start_date, end_date, resample_min):
	query = f"SELECT f_tag_name, f_timestamp, f_value, f_insight_type FROM \
		tb_rb_insight_lstm WHERE f_tag_name = '{tag_name}' AND cast(f_date_rec as date) \
		BETWEEN '{start_date}' AND '{end_date}'"
	result_df = pd.read_sql(query, con=engine)
	
	if result_df.empty:
		raise Exception('Data is unavailable.')

	result_df["f_value"] = pd.to_numeric(result_df["f_value"])
	result_df.set_index('f_timestamp', inplace=True)
	result_df.sort_index(ascending=True, inplace=True)

	return result_df

def get_survival_data(engine, equipment, n_prediction):
	query = f"SELECT te.f_equipment_id, te.f_equipment_name, ts.f_timestamp, ts.f_survival_type, ts.f_value \
		FROM tb_rb_survival ts INNER JOIN db_soket.tb_im_equipments te ON te.f_equipment_id = ts.f_equipment_id \
		WHERE te.f_equipment_name = '{equipment}'"
	result_df = pd.read_sql(query, con=engine)
	result_df["f_value"] = pd.to_numeric(result_df["f_value"])
	result_df.set_index('f_timestamp', inplace=True)
	result_df.sort_index(ascending=True, inplace=True)
	result_df.tail(n_prediction)

	return result_df

def get_anomaly_interval_data(engine, time_interval):
	query = f"SELECT f_tag_name, f_timestamp, f_value, f_status_limit FROM \
		tb_rb_anomaly WHERE f_equipment_id <> '0' AND f_timestamp >= NOW() - INTERVAL {time_interval} HOUR"
	result_df = pd.read_sql(query, con=engine)

	return result_df

def get_sensor_information_from_unit(engine, unit):
	query = f"SELECT u.f_unit_name, e.f_equipment_name_alt1 f_system, e.f_equipment_name f_equipment, \
		t.f_tag_name f_tag_name, t.f_l1_alarm, t.f_h1_alarm FROM db_soket.tb_im_units u \
		INNER JOIN db_soket.tb_im_equipments e \
		ON u.f_unit_id = e.f_unit_id \
		INNER JOIN db_soket.tb_im_tags t ON e.f_equipment_id = t.f_equipment_id \
		WHERE u.f_unit_name = '{unit}'"
	result_df = pd.read_sql(query, con=engine)

	return result_df

def close_conn(engine):
	engine.dispose()