# model.py
# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout
from keras.utils import plot_model
import math
from sklearn.metrics import mean_squared_error
from config import DATA_PATH, MODEL_SAVE_PATH, MODEL_PLOT_PATH, MODEL_SHAPES_PLOT_PATH

# 데이터 로딩
dataset = pd.read_csv(DATA_PATH, index_col='Date', parse_dates=['Date'], encoding='utf-8')

# 데이터 전처리
training_set = dataset[:'2016'].iloc[:, 1:2].values
test_set = dataset['2017':].iloc[:, 1:2].values

# 스케일링
sc = MinMaxScaler(feature_range=(0, 1))
training_set_scaled = sc.fit_transform(training_set)

# LSTM 입력 데이터 준비
X_train, y_train = [], []
for i in range(60, len(training_set)):
    X_train.append(training_set_scaled[i-60:i, 0])
    y_train.append(training_set_scaled[i, 0])
X_train, y_train = np.array(X_train), np.array(y_train)
X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))

# 모델 구축
regressor = Sequential([
    LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], 1)),
    Dropout(0.2),
    LSTM(units=50, return_sequences=True),
    Dropout(0.2),
    LSTM(units=50, return_sequences=True),
    Dropout(0.2),
    LSTM(units=50),
    Dropout(0.2),
    Dense(units=1)
])

# 모델 컴파일 및 학습
regressor.compile(optimizer='rmsprop', loss='mean_squared_error')
regressor.fit(X_train, y_train, epochs=2, batch_size=32)

# 모델 저장
regressor.save(MODEL_SAVE_PATH)
print(f"Model saved to '{MODEL_SAVE_PATH}'")

# 모델 구조 이미지 생성
plot_model(regressor, to_file=MODEL_PLOT_PATH)
plot_model(regressor, to_file=MODEL_SHAPES_PLOT_PATH, show_shapes=True)
print(f"Model structure saved to '{MODEL_PLOT_PATH}' and '{MODEL_SHAPES_PLOT_PATH}'")
