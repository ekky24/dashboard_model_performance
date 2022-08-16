import pandas as pd
import numpy as np

def handle_nan_in_sensor_df(sensor_df, menit, start_date, end_date):
	# Replace the outliers with NaNs. This in necessery, in order to consolidate the all sources of bad values int NaN indicators.
	dataset_dates_set = set(sensor_df.index)
	all_dates = pd.Series(data=pd.date_range(start=start_date, end=end_date, freq=f'{menit}min'))

	all_data = np.empty((all_dates.shape[0], sensor_df.shape[1]))

	all_data[:] = np.nan
	for i in range(all_dates.shape[0]):
		date = all_dates[i]

		if date in dataset_dates_set:
			all_data[i, :] = sensor_df.loc[date].values

	sensor_df = pd.DataFrame(all_data, columns=sensor_df.columns, index=all_dates)
	sensor_df.interpolate(method='time', limit_direction='both', inplace=True)
	sensor_df.interpolate(method='pad', inplace=True)
	sensor_df.fillna(value=0, inplace=True)

	return sensor_df

def detect_and_label_outliers_as_nan(data, m=2):
	for column in data.columns:
		d = np.abs(data[column] - np.mean(data[column]))
		mdev = np.mean(d)
		s = d/mdev if mdev else np.zeros(d.shape)
		data.loc[s > m, column] = np.NaN

	return data

def outlier_calculator(data, m=2):
	n_outlier = {}
	outlier_data = data.copy()
	data_without_outlier = data.copy()

	for column in data.columns:
		orig_n_data = int(data[[column]].isna().sum().values[0])
		d = np.abs(data[column] - np.mean(data[column]))
		mdev = np.mean(d)
		s = d/mdev if mdev else np.zeros(d.shape)
		data_without_outlier.loc[s > m, column] = np.NaN
		outlier_data.loc[s <= m, column] = np.NaN
		outlier_n_data = int(data_without_outlier[[column]].isna().sum().values[0])

		n_outlier[column] = outlier_n_data - orig_n_data
	return outlier_data, n_outlier

def ordering_data(df, sensor_list):
	ordered_dict = {}
	for sensor in sensor_list:
		try:
			ordered_dict[sensor] = df.loc[:, sensor]
		except KeyError:
			ordered_dict[sensor] = pd.Series(np.zeros(df.shape[0]), index=df.index)

	ordered_df = pd.DataFrame(ordered_dict)
	return ordered_df