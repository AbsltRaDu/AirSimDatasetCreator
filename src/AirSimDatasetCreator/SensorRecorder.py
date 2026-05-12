import threading
import time

import numpy as np
import airsim


from src.AirSimDatasetCreator.AirSimDroneConnector import AirSimDroneConnector
from src.AirSimDatasetCreator.DatasetWriterEuRoCLike import EuRoCDatasetWriter

class SensorRecorder:
    '''
    Получает данные из AirSim и передает их writer.
    '''

    def __init__(self, cam_client: AirSimDroneConnector, imu_client: AirSimDroneConnector, writer: EuRoCDatasetWriter, cam0_name: str = "cam0", cam1_name: str = "cam1"):
        # self.drone = drone
        self.writer = writer
        self.cam_client = cam_client
        self.imu_client = imu_client
        self.cam0_name = cam0_name
        self.cam1_name = cam1_name
        
        self._imu_thread = None
        self._imu_stop_event = threading.Event()

    def record_imu(self):
        imu = self.imu_client.getImuData() # Отдельный клиент для записи IMU

        timestamp_ns = imu.time_stamp

        angular = imu.angular_velocity
        linear = imu.linear_acceleration

        self.writer.write_imu_row(
            timestamp_ns,
            angular.x_val,
            angular.y_val,
            angular.z_val,
            linear.x_val,
            linear.y_val,
            linear.z_val,
        )

    def start_imu_recording(self, imu_hz=200):
        '''
        Отдельный поток записи IMU
        '''
        
        self._imu_stop_event.clear()
        
        def imu_loop():
            dt = 1 / imu_hz
            next_time = time.perf_counter()
            
            while not self._imu_stop_event.is_set():
                now = time.perf_counter()
                
                if now >= next_time:
                    self.record_imu()
                    next_time += dt
                
                time.sleep(0.0005)
                
        self._imu_thread = threading.Thread(target=imu_loop)
        self._imu_thread.start()
        
    def stop_imu_recording(self):
        '''
        Останавливаем IMU поток
        '''
        
        self._imu_stop_event.set()
        
        if self._imu_thread is not None:
            self._imu_thread.join()
        
    
    def record_stereo_images(self, ):
        """
        Считывает пару RGB-изображений из AirSim и сохраняет их как cam0/cam1.
        """
        responses = self.cam_client.simGetImages([
            airsim.ImageRequest(self.cam0_name, airsim.ImageType.Scene, pixels_as_float=False, compress=False),
            airsim.ImageRequest(self.cam1_name, airsim.ImageType.Scene, pixels_as_float=False, compress=False),
        ])

        if len(responses) != 2:
            raise RuntimeError(f"Ожидались 2 изображения, получено: {len(responses)}")

        for camera_name_euroc, response in zip(["cam0", "cam1"], responses):
            if response.width == 0 or response.height == 0:
                raise RuntimeError(
                    f"Камера {camera_name_euroc} вернула пустое изображение. "
                    f"Проверь имя камеры в settings.json."
                )

            timestamp_ns = response.time_stamp

            # image_data_uint8 — это плоский массив байт длиной H * W * 3.
            image_1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)

            # Превращаем плоский массив в изображение H x W x 3.
            image_rgb = image_1d.reshape(response.height, response.width, 3)

            self.writer.write_camera_image(
                camera_name=camera_name_euroc,
                timestamp_ns=timestamp_ns,
                image_rgb=image_rgb,
            )
    
    def record_ground_truth(self):
        state = self.cam_client.getMultirotorState()

        timestamp_ns = state.timestamp

        pos = state.kinematics_estimated.position
        orient = state.kinematics_estimated.orientation
        vel = state.kinematics_estimated.linear_velocity

        self.writer.write_gt_row(
            timestamp_ns,
            pos.x_val,
            pos.y_val,
            pos.z_val,
            orient.w_val,
            orient.x_val,
            orient.y_val,
            orient.z_val,
            vel.x_val,
            vel.y_val,
            vel.z_val,
        )
        
    def record_once(self):
        '''
        Записывает один синхронный срез данных.
        '''
        
        # self.record_imu() # убрал, потому что теперь отдельным поток пишем imu
        self.record_ground_truth()
        self.record_stereo_images()