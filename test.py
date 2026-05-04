import airsim

client = airsim.MultirotorClient(ip="172.31.240.1", port=41451)
client.confirmConnection()

print('Соединение установлено')

client.enableApiControl(True) # Врубаем APi
print('API подключено')
client.armDisarm(True) # Включение моторов
print('Моторы включены')
client.takeoffAsync().join() # Взлет
print('Взлет')

print('Начато движение к цели')

client.moveToPositionAsync(
    x=10,
    y=0,
    z=-5,
    velocity=3
).join()

print('Движение завершено')


print('Выполняю посадку')
client.landAsync().join() # Посадка
print('Выключаю моторы')
client.armDisarm(False) # Выключение моторов
print('Отключаю API')
client.enableApiControl(False) # отрубаем API


