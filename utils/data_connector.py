import pandas as pd
import numpy as np
import sqlalchemy as db
from credentials.db_credentials import DB_SERVER, DB_LOCAL, DB_UNIT_MAPPER, TB_MAPPER

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

def close_conn(engine):
	engine.dispose()