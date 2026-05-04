import airsim
import time
import os 
import cv2
import numpy as np

client = airsim.MultirotorClient(ip="172.31.240.1", port=41451)
client.confirmConnection()

print('Соединение установлено')

client.enableApiControl(True) # Врубаем APi
print('API подключено')
client.armDisarm(True) # Включение моторов
print('Моторы включены')
client.takeoffAsync().join() # Взлет
print('Взлет')

os.makedirs('dataset_0/cam0/data', exist_ok=True)
os.makedirs('dataset_0/cam1/data', exist_ok=True)

for i in range(100):
    
    timestamp = int(time.time() * 1e9)  # наносекунды как в EuRoC
    
    # Получаем изображения
    responses = client.simGetImages([
        airsim.ImageRequest('0', airsim.ImageType.Scene, False, False),
        airsim.ImageRequest('1', airsim.ImageType.Scene, False, False)
    ])
    
    # Обрабатываем изображения
    img0 = np.frombuffer(responses[0].image_data_uint8, dtype=np.uint8)
    img0 = img0.reshape(responses[0].height, responses[0].width, 3)
    
    img1 = np.frombuffer(responses[1].image_data_uint8, dtype=np.uint8)
    img1 = img1.reshape(responses[1].height, responses[1].width, 3)

    # сохранение
    cv2.imwrite(f"dataset_0/cam0/data/{timestamp}.png", img0)
    cv2.imwrite(f"dataset_0/cam1/data/{timestamp}.png", img1)

    # TODO частоты не как в EuRoC
    imu = client.getImuData()
    # TODO координаты не как в EuRoC
    pose = client.simGetVehiclePose()
    
    print('IMU:', imu)
    print('Pose:', pose)
    
    time.sleep(0.1)
    
# print('Начато движение к цели')

# client.moveToPositionAsync(
#     x=10,
#     y=0,
#     z=-5,
#     velocity=3
# ).join()

# print('Движение завершено')


print('Выполняю посадку')
client.landAsync().join() # Посадка
print('Выключаю моторы')
client.armDisarm(False) # Выключение моторов
print('Отключаю API')
client.enableApiControl(False) # отрубаем API


