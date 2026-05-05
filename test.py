
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


from src.AirSimDatasetCreator.AirSimDroneConnector import AirSimDroneConnector
from src.AirSimDatasetCreator.DatasetWriterEuRoCLike import EuRoCDatasetWriter
from src.AirSimDatasetCreator.SensorRecorder import SensorRecorder
from src.AirSimDatasetCreator.TrajectoryExecuter import TrajectoryExecutor


commands = [
        {
            "type": "takeoff",
            "timeout_sec": 10,
        },
        {
            "type": "move_to",
            "x": 0.0,
            "y": 0.0,
            "z": -3.0,
            "velocity": 1.0,
        },
        {
            "type": "velocity_body",
            "vx": 1.0,
            "vy": 0.0,
            "vz": 0.0,
            "duration": 3.0,
        },
        {
            "type": "yaw_rate",
            "yaw_rate": 20.0,
            "duration": 2.0,
        },
        {
            "type": "velocity_z",
            "vx": 1.0,
            "vy": 0.0,
            "z": -3.0,
            "duration": 3.0,
        },
        {
            "type": "hover",
            "duration": 2.0,
        },
        {
            "type": "land",
            "timeout_sec": 10,
        },
    ]

drone = AirSimDroneConnector(ip='192.168.160.1', port=41451)
drone.enable()

writer = EuRoCDatasetWriter(root_dir='dataset_test')
writer.create_structure()
writer.init_csv_files()
writer.write_command_log(commands)

recorder = SensorRecorder(drone=drone, writer=writer)
executer = TrajectoryExecutor(drone=drone, recorder=recorder)

try: 
    command_log = executer.execute(commands)
    
    print('---ЛОГ выполненых команд---')
    print(*command_log, sep='\n--')
    
finally:
    drone.disable()
