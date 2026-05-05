import json

import airsim

from src.AirSimDatasetCreator.AirSimDroneConnector import AirSimDroneConnector
from src.AirSimDatasetCreator.DatasetWriterEuRoCLike import EuRoCDatasetWriter
from src.AirSimDatasetCreator.SensorRecorder import SensorRecorder
from src.AirSimDatasetCreator.TrajectoryExecuter import TrajectoryExecutor

from source.IP import LAPTOP_IP, DESKTOP_IP


with open('trajectories/fast_short_commands.json', 'r', encoding='utf-8') as f:
    dct = json.load(f)
    
for _dct in dct['trajectories']:
    print(f"Выполняется симуляция {_dct['description']}")
    commands = _dct['commands']

    drone = AirSimDroneConnector(ip=DESKTOP_IP, port=41451)
    drone.enable()


    sensor_client = airsim.MultirotorClient(ip=DESKTOP_IP, port=41451)
    sensor_client.confirmConnection()

    writer = EuRoCDatasetWriter(root_dir='dataset_test_train', dataset_name=f"mav_{_dct['id']}")
    writer.create_structure()
    writer.init_csv_files()
    writer.write_command_log(commands)

    recorder = SensorRecorder(sensor_client, writer=writer)
    executer = TrajectoryExecutor(drone=drone, recorder=recorder)

    try: 
        command_log = executer.execute(commands)
        
        print('---ЛОГ выполненых команд---')
        print(*command_log, sep='\n--')
        
    finally:
        drone.disable()
