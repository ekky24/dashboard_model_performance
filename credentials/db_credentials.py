# DB_SERVER = {
#     'host': '127.0.0.1:15801',
#     'username': 'ds',
#     'password': 'ds@Sml23'
# }

DB_SERVER = {
    'host': '10.7.1.116:3307',
    'username': 'ds',
    'password': 'ds@Sml23'
}

DB_LOCAL = {
    'host': '127.0.0.1',
    'username': 'root',
    'password': ''
}

DB_UNIT_MAPPER = {
	'DB_SOKET': 'db_soket',
	'PAITON1': 'db_paiton_1',
	'PAITON2': 'db_paiton_2',
	'TNY1': 'db_tny',
	'TNY2': 'db_tny',
	'TAA1': 'db_tja',
	'TAA2': 'db_tja',
	'UJPCT1': 'db_pacitan_1',
	'UJPCT2': 'db_pacitan_2',
	'UJPCT_COMMON': 'db_pacitan_1',
	'UPBRS_SENGGURUH_1': 'db_brs_sengguruh_1',
	'UPBRS_SENGGURUH_2': 'db_brs_sengguruh_2',
	'UPBRS_SUTAMI_1': 'db_brs_sutami_1',
	'UPBRS_SUTAMI_2': 'db_brs_sutami_2',
	'UPBRS_SUTAMI_3': 'db_brs_sutami_3',
	'UPBRS_TULUNGAGUNG_1': 'db_brs_tulungagung_1',
	'UPBRS_TULUNGAGUNG_2': 'db_brs_tulungagung_2',
	'UJKTT_1': 'db_kaltim_1',
	'UJKTT_2': 'db_kaltim_2',
	'UJRBG_1': 'db_rembang_1',
	'UJRBG_2': 'db_rembang_2',
	'UJLJ_BOLOK_1': 'db_bolok_1',
	'UJLJ_BOLOK_2': 'db_bolok_2',
	'UJLJ_BTG_1': 'db_belitung_1',
	'UJLJ_BTG_2': 'db_belitung_2',
	'UJLJ_AMG_1': 'db_amurang_1',
	'UJLJ_AMG_2': 'db_amurang_2',
	'UJPS_1': 'db_pulpis_1',
	'UJPS_2': 'db_pulpis_2',
	'UJBK_1': 'db_bangka_1',
	'UJBK_2': 'db_bangka_2',
	'UJTD_1': 'db_tidore_1',
	'UJTD_2': 'db_tidore_2',
	'UJKD_1': 'db_kendari_1',
	'UJKD_2': 'db_kendari_2',
	'UJRP_1': 'db_ropa_1',
    'UJRP_2': 'db_ropa_2',
    'UJKP_1': 'db_ketapang_1',
    'UJKP_2': 'db_ketapang_2',
    'UJTB_1': 'db_tembilahan_1',
    'UJTB_2': 'db_tembilahan_2',
}

TB_MAPPER = {
	'equipment_mapper': 'tb_im_equipments',
}

SSH_MAPPER = {
	'testing': {
		'read': {
			'ssh': '10.7.1.116',
			'ssh_port': 22055,
			'username': 'apps',
			'password': 'Soket2023!',
			'remote_access': '127.0.0.1',
			'remote_access_port': 3306,
			'local_access': '127.0.0.1',
			'local_access_port': 15801,
		},
	},
}