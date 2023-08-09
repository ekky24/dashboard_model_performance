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