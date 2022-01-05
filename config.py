RAW_DATA_RESAMPLE_MIN = 5
ANOMALY_RESAMPLE_MIN = 5
FUTURE_PREDICTION_RESAMPLE_MIN = 10

FUTURE_PREDICTION_INPUT_STEP = 72
FUTURE_PREDICTION_OUTPUT_STEP = 48
FUTURE_PREDICTION_ALPHA = 0.1

SURVIVAL_N_PREDICTION = 365

OUTLIER_SIGMA = 3
TEMP_FOLDER = 'temp'
HISTORIAN_DATA_FOLDER = 'data/historian_data'

UNIT_NAME_MAPPER = {
    'PLTU Paiton 1': 'UJPAITON1',
    'PLTU Paiton 2': 'UJPAITON2',
    'PLTU Tenayan 1': 'UJTNY1',
    'PLTU Tenayan 2': 'UJTNY2',
    'PLTU Tanjung Awar-Awar 1': 'UJTAW1',
    'PLTU Tanjung Awar-Awar 2': 'UJTAW2',
    'PLTU Pacitan 1': 'UJPCT1',
    'PLTU Pacitan 2': 'UJPCT2',
    'PLTA Sengguruh 1': 'UPBRS_SENGGURUH_1',
    'PLTA Sengguruh 2': 'UPBRS_SENGGURUH_2',
    'PLTA Sutami 1': 'UPBRS_SUTAMI_1',
    'PLTA Sutami 2': 'UPBRS_SUTAMI_2',
    'PLTA Sutami 3': 'UPBRS_SUTAMI_3',
    'PLTA T.Agung 1': 'UPBRS_TULUNGAGUNG_1',
    'PLTA T.Agung 2': 'UPBRS_TULUNGAGUNG_2',
    'PLTU Kaltim Teluk 1': 'UJKTT_1',
    'PLTU Kaltim Teluk 2': 'UJKTT_2',
    'PLTU Rembang 1': 'UJRBG_1',
    'PLTU Rembang 2': 'UJRBG_2',
    'PLTU Bolok 1': 'UJLJ_BOLOK_1',
    'PLTU Bolok 2': 'UJLJ_BOLOK_2',
    'PLTU Belitung 1': 'UJLJ_BTG_1',
    'PLTU Belitung 2': 'UJLJ_BTG_2',
    'PLTU Amurang 1': 'UJLJ_AMG_1',
    'PLTU Amurang 2': 'UJLJ_AMG_2',
}