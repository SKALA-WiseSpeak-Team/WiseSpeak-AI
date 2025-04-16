# config.py
import os

# 기본 경로 설정
BASE_DIR = os.getenv("BASE_DIR", "C:/Users/82109/Desktop/model_serving_rpt/server")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_files/")
MODEL_DIR = os.path.join(BASE_DIR, "model/")
IMAGE_DIR = os.path.join(BASE_DIR, "view-model-architecture/")
MODEL_IMG_DIR = os.path.join(BASE_DIR, "model-images/")

# 파일 경로
DATA_PATH = os.path.join(UPLOAD_DIR, "IBM_2006-01-01_to_2018-01-01.csv")
MODEL_SAVE_PATH = os.path.join(MODEL_DIR, "result/stock_lstm_model.keras")
MODEL_PLOT_PATH = os.path.join(IMAGE_DIR, "model.png")
MODEL_SHAPES_PLOT_PATH = os.path.join(IMAGE_DIR, "shapes/model_shapes.png")
PREDICTION_PLOT_PATH = os.path.join(IMAGE_DIR, "stock.png")