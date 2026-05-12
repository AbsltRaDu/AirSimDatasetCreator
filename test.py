import json

import airsim

from src.AirSimDatasetCreator.AirSimDroneConnector import AirSimDroneConnector
from src.AirSimDatasetCreator.DatasetWriterEuRoCLike import EuRoCDatasetWriter
from src.AirSimDatasetCreator.SensorRecorder import SensorRecorder
from src.AirSimDatasetCreator.TrajectoryExecuter import TrajectoryExecutor

from source.IP import DESKTOP_IP


with open('trajectories/easy_rotation_commands.json', 'r', encoding='utf-8') as f:
    dct = json.load(f)
    
for _dct in dct['trajectories']:
    print(f"Выполняется симуляция {_dct['description']}")
    commands = _dct['commands']

    drone = AirSimDroneConnector(ip=DESKTOP_IP, port=41451)
    drone.enable()


    cam_client = airsim.MultirotorClient(ip=DESKTOP_IP, port=41451)
    cam_client.confirmConnection()
    
    imu_client = airsim.MultirotorClient(ip=DESKTOP_IP, port=41451)
    imu_client.confirmConnection()

    writer = EuRoCDatasetWriter(root_dir='dataset_test_train', dataset_name=f"mav_{_dct['id']}")
    writer.create_structure()
    writer.init_csv_files()
    writer.write_command_log(commands)

    recorder = SensorRecorder(cam_client, imu_client=imu_client, writer=writer, cam0_name='cam0', cam1_name='cam1')
    executer = TrajectoryExecutor(drone=drone, recorder=recorder)

    
    recorder.start_imu_recording(imu_hz=200) # Теперь отдельный поток, поэтому отдельная запись
    try: 
        command_log = executer.execute(commands)
        
        print('---ЛОГ выполненых команд---')
        print(*command_log, sep='\n--')
        
    finally:
        recorder.stop_imu_recording() # Вырубаем поток записи IMU
        drone.disable()
