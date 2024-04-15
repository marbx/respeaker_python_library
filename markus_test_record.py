'''
sudo apt install python3-pyaudio python3-requests

NICHT!!!!!!!!
  sudo apt install python3-pip
  pip install pyaudio requests


'''

import os
import wave
import types
import collections
import string
from threading import Thread, Event

import queue as Queue

import pyaudio

class Microphone:
    sample_rate = 16000
    frames_per_buffer = 512
    listening_mask = (1 << 0)
    detecting_mask = (1 << 1)
    recording_mask = (1 << 2)

    def __init__(self, pyaudio_instance=None, quit_event=None, decoder=None):

        self.pyaudio_instance = pyaudio_instance if pyaudio_instance else pyaudio.PyAudio()

        self.device_index = None
        for i in range(self.pyaudio_instance.get_device_count()):
            dev = self.pyaudio_instance.get_device_info_by_index(i)
            name = dev['name'].encode('utf-8')
            print('... init name {}'.format(name))
            print(i, name, dev['maxInputChannels'], dev['maxOutputChannels'])
            if name.lower().find(b'respeaker') >= 0 and dev['maxInputChannels'] > 0:
                print('... init use {}'.format(name))
                self.device_index = i
                break

        if not self.device_index:
            device = self.pyaudio_instance.get_default_input_device_info()
            self.device_index = device['index']
        self.stream = self.pyaudio_instance.open(
            input=True,
            start=False,
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            frames_per_buffer=self.frames_per_buffer,
            stream_callback=self._callback,
            input_device_index=self.device_index,
        )

        self.quit_event = quit_event if quit_event else Event()


        self.status = 0
        self.active = False


        self.wav = None
        self.record_countdown = None
        self.listen_countdown = [0, 0]


    def record(self, file_name, seconds=1800):
        self.wav = wave.open(file_name, 'wb')
        self.wav.setsampwidth(2)
        self.wav.setnchannels(1)
        self.wav.setframerate(self.sample_rate)
        self.record_countdown = (seconds * self.sample_rate + self.frames_per_buffer - 1) / self.frames_per_buffer
        self.status |= self.recording_mask
        self.start()

    def quit(self):
        self.status = 0
        self.quit_event.set()
        self.listen_queue.put('')
        if self.wav:
            self.wav.close()
            self.wav = None

    def start(self):
        if self.stream.is_stopped():
            self.stream.start_stream()

    def stop(self):
        if not self.status and self.stream.is_active():
            self.stream.stop_stream()

    def close(self):
        self.quit()
        self.stream.close()

    def _callback(self, in_data, frame_count, time_info, status):
        if self.status & self.recording_mask:
            self.wav.writeframes(in_data)
            self.record_countdown -= 1
            if self.record_countdown <= 0:
                self.status &= ~self.recording_mask
                self.wav.close()

        return None, pyaudio.paContinue




def test_record():
    import time

    mic = Microphone()
    mic.record('markus.wav', seconds=3)
    time.sleep(3)
    mic.quit()


if __name__ == '__main__':
    test_record()
