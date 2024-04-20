import logging
import socket
import pyaudio
import wave
import numpy as np

CHUNK = 88200
RATE = 88200

logging.basicConfig(level=logging.INFO)



def connect_to_server():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_ip = input("Введите айпи сервера: ")
        server_port = int(input("Введите порт сервера: "))

        client.connect((server_ip, server_port))
        logging.info('Успешное подключение к серверу')

    except ConnectionError as e:
        logging.error(f'Ошибка подключения к серверу: {e}')
    except Exception as e:
        logging.error(f'Произошла ошибка: {e}')

    return client


client = connect_to_server()

FORMAT = pyaudio.paInt16
CHANNELS = 1



p = pyaudio.PyAudio()
stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)



while True:
    try:
        data = client.recv(CHUNK)

        stream.write(data)
    except KeyboardInterrupt:
        break


stream.stop_stream()
stream.close()
p.terminate()
client.close()

print("Нажмите любую клавишу...")
input()
