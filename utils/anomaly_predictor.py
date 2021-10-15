import config
import pandas as pd
import numpy as np
import joblib
from tensorflow.keras.models import load_model
from sklearn.metrics import mean_absolute_error

def get_historian_data(unit, system, equipment, start_date, end_date):
	historian_path = f"{config.HISTORIAN_DATA_FOLDER}/{unit}/{system}/{equipment}.csv"
	historian_df = pd.read_csv(historian_path, index_col='timestamp', parse_dates=['timestamp'])
	historian_df = historian_df.loc[start_date:end_date]
	historian_df = historian_df.resample(f'{config.ANOMALY_RESAMPLE_MIN}min').mean()
	historian_df.interpolate(method='time', limit_direction='both', inplace=True)

	return historian_df

def get_model(unit, system, equipment, tags):
	system = system.replace('&', 'AND')
	equipment = equipment.replace('&', 'AND')
	model_path = f'trained_models/anomaly_detection/{config.UNIT_NAME_MAPPER[unit]}/{system}/{equipment}'
	scaler = joblib.load(f'{model_path}/scaler_univariate_{equipment}.pkl')
	sensor_list = pd.read_csv(f'{model_path}/sensor_list_{equipment}.csv')
	sensor_list = sensor_list.iloc[:,0].values

	models = {}
	for tag in tags:
		models[tag] = load_model(f'{model_path}/model_{equipment}_{tag}.h5')

	return scaler, sensor_list, models

def calculate_limits(y_true_df, y_pred_df, sigma=2.576):
	LLs = np.zeros(y_true_df.shape)
	ULs = np.zeros(y_true_df.shape)
	for idx, col in enumerate(y_true_df.columns):
		curr_y_true = y_true_df.values[:, idx]
		curr_y_pred = y_pred_df.values[:, idx]

		reconstruction_error = mean_absolute_error(curr_y_true, curr_y_pred)
		deviation = np.std(curr_y_true - curr_y_pred)
		LL = curr_y_pred - (reconstruction_error + sigma * deviation)
		UL = curr_y_pred + (reconstruction_error + sigma * deviation)

		LLs[:, idx] = LL
		ULs[:, idx] = UL

	LL_df = pd.DataFrame(LLs, columns=y_true_df.columns, index=y_true_df.index)
	UL_df = pd.DataFrame(ULs, columns=y_true_df.columns, index=y_true_df.index)
	return LL_df, UL_df

def detect_anomalies(y_true_df, LL_df, UL_df):
	anomaly_lower = y_true_df.copy()
	anomaly_upper = y_true_df.copy()

	for idx, col in enumerate(y_true_df.columns):
		curr_anomaly_lower = anomaly_lower.values[:, idx]
		curr_LL = LL_df.values[:, idx]
		curr_anomaly_lower[curr_anomaly_lower > curr_LL] = np.nan

		curr_anomaly_upper = anomaly_upper.values[:, idx]
		curr_UL = UL_df.values[:, idx]
		curr_anomaly_upper[curr_anomaly_upper < curr_UL] = np.nan

	return anomaly_lower, anomaly_upper

def create_lstm_sequence(data, timesteps=72):
    """
    Convert input data into 3-D array as required for LSTM network.
    --------------------------------------------
    Input
    Data : 2D array data 
    timesteps : timesteps / lag number
    ---------------------------------------------
    Output
    datareturn1 : A 3D array for lstm, where the array is sample x timesteps x features.
    """
    datareturn1 = []
    for i in range(timesteps, len(data)):
        d1 = data[i - timesteps:i]
        if np.max(np.isnan(data[i - timesteps:i + 1])):
            continue
        datareturn1.append(d1)
    datareturn1 = np.array(datareturn1)
    return datareturn1

def flatten_to_2d(X):
    '''
    Flatten a 3D array.
    --------------------------------------------
    Input
    X : A 3D array for lstm, where the array is sample x timesteps x features.
    --------------------------------------------
    Output
    flattened_X : A 2D array, sample x features.
    '''
    n = X.shape[0] + X.shape[1]
    timesteps = X.shape[1]
    features = X.shape[2]
    flattened_X = np.empty((n-1, features))  # sample x features array.
    flattened_X[:timesteps] = X[0,:,:]
    for i in range(timesteps, n-1):
        flattened_X[i] = X[i-timesteps+1, (timesteps-1), :]
    return(flattened_X)