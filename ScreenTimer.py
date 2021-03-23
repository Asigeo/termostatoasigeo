import asyncio
from select import select

from rpi_backlight import Backlight
from evdev import InputDevice, categorize, ecodes
import codecs
import time
from threading import Thread, Semaphore


class ScreenTimer:
    def __init__(self):
        self.contador = 0
        self.th1 = Thread(target=self.reader)
        self.th2 = Thread(target=self.counter)
        self.mut = Semaphore(1)
        self.back = Backlight()
        self.th1.start()
        self.th2.start()

    def counter(self):
        while (True):
            time.sleep(1)
            self.mut.acquire()
            self.contador = self.contador + 1
            print(self.contador)
            if self.contador == 60:
                self.back.power = False


            self.mut.release()

    def reader(self):

        dev = InputDevice('/dev/input/event0')

        while True:
            r, _, _ = select([dev], [], [])
            self.mut.acquire()
            self.back.power = True
            self.contador = 0
            self.mut.release()
            time.sleep(1)
            for ev in dev.read():
                print(ev)


if __name__ == '__main__':
    ScreenTimer()