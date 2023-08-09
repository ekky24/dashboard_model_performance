RAW_DATA_RESAMPLE_MIN = 5
ANOMALY_RESAMPLE_MIN = 5
FUTURE_PREDICTION_RESAMPLE_MIN = 10

FUTURE_PREDICTION_INPUT_STEP = 72
FUTURE_PREDICTION_OUTPUT_STEP = 48
FUTURE_PREDICTION_ALPHA = 0.1

SURVIVAL_N_PREDICTION = 365

OUTLIER_SIGMA = 3
TEMP_FOLDER = 'temp'
DATA_FOLDER = 'data'
HISTORIAN_DATA_FOLDER = 'data/historian_data'
ANOMALY_DETECTION_DUMP_FOLDER = 'result/anomaly_detection_dump'
BAD_MODEL_LIST_DUMP_FOLDER = 'result/bad_model_table_dump'
HOST_URL = '35.219.48.62'

UNIT_NAME_MAPPER = {
    'PLTU Paiton 1': 'PAITON1',
    'PLTU Paiton 2': 'PAITON2',
    'PLTU Tenayan 1': 'TNY1',
    'PLTU Tenayan 2': 'TNY2',
    'PLTU Tanjung Awar-Awar 1': 'TAA1',
    'PLTU Tanjung Awar-Awar 2': 'TAA2',
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
    'PLTU Pulang Pisau 1': 'UJPS_1',
    'PLTU Pulang Pisau 2': 'UJPS_2',
    'PLTU Bangka 1': 'UJBK_1',
    'PLTU Bangka 2': 'UJBK_2',
    'PLTU Tidore 1': 'UJTD_1',
    'PLTU Tidore 2': 'UJTD_2',
    'PLTU Kendari 1': 'UJKD_1',
    'PLTU Kendari 2': 'UJKD_2',
}

TIMEZONE_MAPPER = {
    'PLTU Paiton 1': 'Asia/Jakarta',
    'PLTU Paiton 2': 'Asia/Jakarta',
    'PLTU Tenayan 1': 'Asia/Jakarta',
    'PLTU Tenayan 2': 'Asia/Jakarta',
    'PLTU Tanjung Awar-Awar 1': 'Asia/Jakarta',
    'PLTU Tanjung Awar-Awar 2': 'Asia/Jakarta',
    'PLTU Pacitan 1': 'Asia/Jakarta',
    'PLTU Pacitan 2': 'Asia/Jakarta',
    'PLTA Sengguruh 1': 'Asia/Jakarta',
    'PLTA Sengguruh 2': 'Asia/Jakarta',
    'PLTA Sutami 1': 'Asia/Jakarta',
    'PLTA Sutami 2': 'Asia/Jakarta',
    'PLTA Sutami 3': 'Asia/Jakarta',
    'PLTA T.Agung 1': 'Asia/Jakarta',
    'PLTA T.Agung 2': 'Asia/Jakarta',
    'PLTU Kaltim Teluk 1': 'Asia/Jakarta',
    'PLTU Kaltim Teluk 2': 'Asia/Jakarta',
    'PLTU Rembang 1': 'Asia/Jakarta',
    'PLTU Rembang 2': 'Asia/Jakarta',
    'PLTU Bolok 1': 'Asia/Jakarta',
    'PLTU Bolok 2': 'Asia/Jakarta',
    'PLTU Belitung 1': 'Asia/Jakarta',
    'PLTU Belitung 2': 'Asia/Jakarta',
    'PLTU Amurang 1': 'Asia/Jakarta',
    'PLTU Amurang 2': 'Asia/Jakarta',
    'PLTU Pulang Pisau 1': 'Asia/Jakarta',
    'PLTU Pulang Pisau 2': 'Asia/Jakarta',
    'PLTU Bangka 1': 'Asia/Jakarta',
    'PLTU Bangka 2': 'Asia/Jakarta',
    'PLTU Tidore 1': 'Asia/Jakarta',
    'PLTU Tidore 2': 'Asia/Jakarta',
    'PLTU Kendari 1': 'Asia/Jakarta',
    'PLTU Kendari 2': 'Asia/Jakarta',
}