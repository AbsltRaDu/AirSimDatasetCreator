import time
import airsim
from typing import Optional
import threading

from src.AirSimDatasetCreator.AirSimDroneConnector import AirSimDroneConnector
from src.AirSimDatasetCreator.SensorRecorder import SensorRecorder

class TrajectoryExecutor:
    '''
    Выполняет заранее заданный список команд движения в виде словарей
    
    
    '''

    def __init__(self, drone: AirSimDroneConnector, recorder: Optional[SensorRecorder] = None):
        self.drone = drone
        self.client = drone.client
        self.recorder = recorder

        self.log_of_command = []
    
    
         
     
    def execute(self, commands):
        
        for number_of_command, command in enumerate(commands):
            
            print(f'Выполняю команду № {number_of_command} - {command["type"]}')
            
            command_type = command["type"]
             
            if command_type == 'takeoff':
                self.log_of_command.append('Взлет')
                self.client.takeoffAsync(timeout_sec=10).join()
            
            elif command_type == 'land':
                self.log_of_command.append('Посадка')
                self.client.landAsync(timeout_sec=10).join()
            
            elif command_type == 'hover':
                self.log_of_command.append('Зависание')
                self.client.hoverAsync().join()
                time.sleep(2.0)
            
            elif command_type == "velocity":
                self.log_of_command.append('Перемещение со скоростью')
                future = self.client.moveByVelocityAsync(command["vx"], command["vy"], command["vz"], command["duration"])
                self._motion_with_record(future, duration=command["duration"])
                
            elif command_type == 'velocity_body':
                self.log_of_command.append('Перемещение со скоростью относительно наблюдателя')
                future = self.client.moveByVelocityBodyFrameAsync(command["vx"], command["vy"], command["vz"], command["duration"])
                self._motion_with_record(future, command["duration"])
                
            elif command_type == 'velocity_z':
                self.log_of_command.append(f"-Перемещение со скоростью на высоте {command['z']}")
                future = self.client.moveByVelocityZAsync(command["vx"], command["vy"], command["z"], command["duration"])
                self._motion_with_record(future, command["duration"])
            
            # TODO проработать сохранение сенсоров с учетом скорости
            elif command_type == 'move_to':
                self.log_of_command.append(f"-Перемещение в точку с координатами ({command['x']}, {command['y']}, {command['z']})")
                future = self.client.moveToPositionAsync(command["x"], command["y"], command["z"], command["velocity"])
                self._motion_with_record_flow(future)
            
            elif command_type == 'yaw_rate':
                self.log_of_command.append(f"-Вращение на {command['yaw_rate'] * command['duration']} градусов")
                future = self.client.rotateByYawRateAsync(command["yaw_rate"], command["duration"])
                self._motion_with_record(future, command["duration"])
            
            # TODO проработать сохранение сенсоров с учетом поворота
            elif command_type == 'yaw_to':
                self.log_of_command.append(f"-Поворот в угол {command['yaw']}")
                future = self.client.rotateToYawAsync(command['yaw'])
                self._motion_with_record_flow(future)
            
            # TODO проработать сохранение сенсоров с учетом скорости
            elif command_type == 'path':
                self.log_of_command.append(f"-Выполняет по пути заданных точек")
                future = self.client.moveOnPathAsync(command['path'], command['velocity'])
                self._motion_with_record_flow(future)

            else:
                raise ValueError(f"Неизвестная команда движения: {command_type}")
        
            
        return self.log_of_command
        
    def _record_checkpoint(self):
        '''
        Записывает один срез сенсоров, если recorder передан.
        Если recorder=None, выполнение траектории идет без записи данных.
        '''
        if self.recorder is not None:
            self.recorder.record_once()
    
          
    def record_during_motion(self, duration, camera_hz=20, gt_hz=20):
        '''
        Записывает сенсоры в течение duration секунд.
        
        duration:
            сколько секунд писать данные.

        imu_hz:
            частота записи IMU.

        camera_hz:
            частота записи stereo-камер.

        gt_hz:
            частота записи ground truth.
        '''

        start_time = time.perf_counter()

        next_camera_time = start_time
        next_gt_time = start_time

        camera_dt = 1.0 / camera_hz
        gt_dt = 1.0 / gt_hz

        while True:
            now = time.perf_counter()

            if now - start_time >= duration:
                break

            if now >= next_gt_time:
                self.recorder.record_ground_truth()
                next_gt_time += gt_dt

            if now >= next_camera_time:
                self.recorder.record_stereo_images()
                next_camera_time += camera_dt

            # Небольшой sleep, чтобы не грузить CPU на 100%.
            time.sleep(0.001)
    
    def _motion_with_record(self, future, duration):
        if self.recorder is not None:
            self.record_during_motion(duration=duration)
        future.join()   
    
    def _motion_with_record_flow(self, future, imu_dt = 1 / 200, cam_dt = 1 / 20):

        stop_event = threading.Event()


        def record_loop():
            """
            Бесконечный цикл записи сенсоров
            Работает параллельно с движением дрона
            """
            next_cam = time.perf_counter()

            # Цикл работает, пока НЕ пришел сигнал остановки
            while not stop_event.is_set():

                now = time.perf_counter()

                # Запись stereo-камер
                if now >= next_cam:
                    
                    # Считываем позицию
                    self.recorder.record_ground_truth()
                    # Считываем cam0 + cam1
                    self.recorder.record_stereo_images()

                    # Планируем следующий кадр
                    next_cam += cam_dt

                time.sleep(0.001)

        # Создаем поток, который будет выполнять record_loop
        thread = threading.Thread(target=record_loop)

        # Запускаем поток
        thread.start()
        
        future.join()
        stop_event.set()
        thread.join()