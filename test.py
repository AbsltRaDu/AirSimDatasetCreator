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