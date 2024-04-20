import os
import socket
import wave
import tkinter as tk
import threading
from tkinter import filedialog
import sounddevice as sd
import time
import numpy as np
import cv2
import pickle
import struct
from pydub import AudioSegment
from gtts import gTTS
import pafy
import requests
import io
import pyaudio
import contextlib

CHUNK = 88200

filepath = ""
conn = []
transmit_audio = True

sample_rate = 88200
marker_interval = 2.5 # Интервал между "биипами" в секундах
beep_duration =  0.8  # Длительность "биипа" в секундах
beep_frequency = 210 # Частота "биипа" в Гц

text = ""


entry = None
entry2 = None
def update_frequency():
    new_frequency = int(entry.get())
    global beep_frequency
    beep_frequency = new_frequency
    print("Значение переменной beep_frequency обновлено:", beep_frequency)


def update_TTS():
    new_frequency = entry2.get()
    global text
    text = new_frequency



marker_on = True


def generate_beep_sound():

    t = np.linspace(0, beep_duration, int(sample_rate * beep_duration), False)


    beep_samples = np.int16(2 * 32767 * np.sin(2 * np.pi * beep_frequency * t))

    return beep_samples


def sendTTS():
    tts = gTTS(text=text, lang='ru', slow=True)
    tts.save("voice.mp3")


    audio = AudioSegment.from_file("voice.mp3", format="mp3")
    audio = audio.set_frame_rate(88200)


    audio.export("voice_44100.wav", format="wav")


    with open("voice_44100.wav", 'rb') as f:
        try:
            while True:
                data = f.read(CHUNK)
                if not data:
                    break
                send_to_all_clients(data)
        except Exception as e:
            print(f"Error in audio transmission: {e}")



def start_marker():


    while marker_on:
        beep_samples = generate_beep_sound()
        send_to_all_clients(beep_samples.tobytes())
        with wave.open("bmarker.wav", 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(beep_samples.tobytes())
        time.sleep(marker_interval)

def select_file():
    global filepath
    filepath = filedialog.askopenfilename(filetypes=[("Wave files", "*.wav")])

def send_to_all_clients(data):
    for client_socket in conn:
        try:
            client_socket.send(data)
        except Exception as e:
            print(f"Error sending message to a client: {e}")
            conn.remove(client_socket)


def start_transmission_from_youtube(url):
    def download_audio(url):
        audio = pafy.new(url)
        bestaudio = audio.getbestaudio()
        audio_stream = requests.get(bestaudio.url, stream=True)

        CHUNK = 1024
        for chunk in audio_stream.iter_content(chunk_size=CHUNK):
            send_to_all_clients(chunk)



    download_audio(url)

def track_duration():
    with wave.open(filepath, 'rb') as f:
        frame_rate = f.getframerate()
        total_frames = f.getnframes()
        duration = total_frames / frame_rate

    return duration


def create_playlist():
    playlist = []
    for file in os.listdir("res"):
        if file.endswith(".wav"):
            playlist.append(os.path.join("res", file))
    return playlist


def play_playlist(playlist):
    global filepath

    for track_path in playlist:

        filepath = track_path

        start_transmission()
        time.sleep(3)



def start_transmission():
    wf = wave.open(filepath, 'rb')

    try:


        while transmit_audio:
            data = wf.readframes(CHUNK)
            if not data:
                break
            send_to_all_clients(data)
    except Exception as e:
        print(f"Error in audio transmission: {e}")
    wf.close()


def stop_transmission():
    global transmit_audio
    transmit_audio = not transmit_audio

def markerhandle():
    global marker_on
    marker_on = not marker_on

def server_thread():

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 223))
    server.listen()
    print("Server started. Waiting for connections...")
    while True:
        sockett, _ = server.accept()
        conn.append(sockett)
        print(f"New client connected: {sockett.getpeername()}")




def toggle_marker():
    print("Значение активности маркера изменено")
    global marker_on
    marker_on = not marker_on


def start_serverInterface():
    threading.Thread(target=server_thread, daemon=True).start()

    # Создаем главное окно
    root = tk.Tk()
    root.geometry('600x400')
    root.title("Сервер")

    # Создаем фрейм для расположения элементов интерфейса в столбик
    frame = tk.Frame(root)
    frame.pack(side='left')

    # Кнопка для выбора файла
    select_button = tk.Button(frame, text="Выбрать файл для трансляции", command=lambda: select_file())
    select_button.pack(side='top')

    start_button = tk.Button(frame, text="Старт трансляции звука",
                             command=lambda: threading.Thread(target=start_transmission,
                                                              daemon=True).start())
    start_button.pack(side='top')

    stop_button = tk.Button(frame, text="Остановить трансляцию/Продолжить трансляцию",
                            command=lambda: stop_transmission())
    stop_button.pack(side='top')

    marker_button = tk.Button(frame, text="Маркер",
                              command=lambda: threading.Thread(target=start_marker, daemon=True).start())
    marker_button.pack(side='top')

    label = tk.Label(frame, text="Введите значение для частоты маркера:")
    label.pack(side='top')

    global entry
    entry = tk.Entry(frame)
    entry.insert(0, str(beep_frequency))
    entry.pack(side='top')

    button = tk.Button(frame, text="Обновить частоту маркера", command=update_frequency)
    button.pack(side='top')

    marker_toggle_button = tk.Button(frame, text="Маркер ON/OFF", command=lambda: markerhandle())
    marker_toggle_button.pack(side='top')





    tts_button = tk.Button(frame, text="Транслировать TTS",
                              command=lambda: threading.Thread(target=sendTTS, daemon=True).start()
                              )

    tts_button.pack(side='top')

    label2 = tk.Label(frame, text="Введите значение текста для TTS:")
    label2.pack(side='top')

    global entry2

    entry2 = tk.Entry(frame)
    entry2.insert(0, str(text))
    entry2.pack(side='top')

    button2 = tk.Button(frame, text="Обновить текст для TTS", command=update_TTS)
    button2.pack(side='top')

    yt_button = tk.Button(frame, text="Транслировать аудио с ютуба",
                           command=lambda: threading.Thread(target=start_transmission_from_youtube, daemon=True, args=("https://www.youtube.com/watch?v=2UjyzLAOfvY",)).start()
                           )

    yt_button.pack(side='top')

    pl_button = tk.Button(frame, text="Проигрывание очереди",
                          command=lambda: threading.Thread(target=play_playlist, daemon=True, args=(
                          create_playlist(),)).start()
                          )

    pl_button.pack(side='top')

    # Запускаем главный цикл обработки событий
    root.mainloop()


start_serverInterface()
