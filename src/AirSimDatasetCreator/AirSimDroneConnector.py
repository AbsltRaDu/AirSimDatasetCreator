from dataclasses import dataclass, field

import airsim

@dataclass
class AirSimDroneConnector:
    '''
    Подключение и базовые команды 
    '''
    
    ip: str
    port: int
    client: airsim.MultirotorClient = field(init=False)
    
    def __post_init__(self):
        self.client = airsim.MultirotorClient(ip=self.ip, port=self.port)
        self.client.confirmConnection()    
     
    def enable(self):
        self.client.enableApiControl(True)
        print('Установлено соединение по API')
        self.client.armDisarm(True)
        print('Вертушки включены')
        
    def takeoff(self, timeout_sec: float = 10.0):
        self.client.takeoffAsync(timeout_sec=timeout_sec).join()
        print('Взлет')
    
    def disable(self):

        self.client.armDisarm(False)
        self.client.enableApiControl(False)
        print('Соединение API разорвано')
    
    def land(self, timeout_sec: float = 10.0):
        self.client.landAsync(timeout_sec=timeout_sec).join()
        print('Посадка')
        
    def stop(self):
        self.client.hoverAsync().join()
    
    def move_by_velocity(self, vx, vy, vz, duration):
        '''
        Движение с заданными скоростями
        '''
        
        self.client.moveByVelocityAsync(vx, vy, vz, duration).join()
        
    
    