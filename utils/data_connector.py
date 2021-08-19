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

def close_conn(engine):
	engine.dispose()