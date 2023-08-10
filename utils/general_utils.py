import pandas as pd
import glob
import numpy as np
import os
import config

def get_tags_data(unit):
	soks = glob.glob(f'{config.DATA_FOLDER}/modeled_tags/*')
	for sok in soks:
		modeled_tags_file = glob.glob(f'{sok}/list_sensor_*.csv')
		modeled_tags_df = pd.read_csv(f'{modeled_tags_file[0]}')

		setting_tags_file = glob.glob(f'{sok}/setting_*.csv')
		setting_tags_df = pd.read_csv(f'{setting_tags_file[0]}')

		units = modeled_tags_df['Unit'].unique().tolist()

		if unit in units:
			break
	
	modeled_tags_df = modeled_tags_df[modeled_tags_df['Unit'] == unit]
	sensors = modeled_tags_df.loc[:, 'Tag Name'].values.tolist()

	setting_tags_df.set_index('f_address_no', inplace=True)
	setting_tags_df = setting_tags_df.loc[sensors]
	setting_tags_df.reset_index(inplace=True)

	return modeled_tags_df, setting_tags_df

def check_flat_data(df):
	std_dev = df.std().values[0]
	if std_dev == 0:
		return True
	else:
		return False

def check_anomaly_perc_big(realtime_df, anomaly_marker_df, threshold_value):
	n_anomaly = anomaly_marker_df.count(axis=0).values[0]
	n_data = realtime_df.shape[0]
	perc_anomaly = n_anomaly / n_data

	if perc_anomaly > threshold_value:
		return True
	else:
		return False

def check_limit_small(realtime_df, lower_limit_df, upper_limit_df, setting_df, threshold_value):
	realtime_std_dev = realtime_df.std().values[0]
	realtime_mean = realtime_df.mean().values[0]
	ll_mean = lower_limit_df.mean().values[0]
	ul_mean = upper_limit_df.mean().values[0]

	realtime_median = realtime_df.median().values[0]
	ll_median = lower_limit_df.median().values[0]
	ul_median = upper_limit_df.median().values[0]

	limit_range = ul_median - ll_median

	setting_std_dev = setting_df['limit_deviation'].values[0]
	upper_estimate_value = realtime_median + threshold_value * realtime_std_dev
	lower_estimate_value = realtime_median - threshold_value * realtime_std_dev
	estimate_range = upper_estimate_value - lower_estimate_value

	if limit_range < estimate_range:
		return True
	else:
		return False

def check_limit_big(realtime_df, lower_limit_df, upper_limit_df, setting_df, threshold_value):
	realtime_std_dev = realtime_df.std().values[0]
	realtime_mean = realtime_df.mean().values[0]
	ll_mean = lower_limit_df.mean().values[0]
	ul_mean = upper_limit_df.mean().values[0]

	realtime_median = realtime_df.median().values[0]
	ll_median = lower_limit_df.median().values[0]
	ul_median = upper_limit_df.median().values[0]

	limit_range = ul_median - ll_median

	setting_std_dev = setting_df['limit_deviation'].values[0]
	upper_estimate_value = realtime_median + threshold_value * realtime_std_dev
	lower_estimate_value = realtime_median - threshold_value * realtime_std_dev
	estimate_range = upper_estimate_value - lower_estimate_value

	if limit_range > estimate_range:
		return True
	else:
		return False