##################################################

#           P26 ----> Relay_Ch1
#			P20 ----> Relay_Ch2
#			P21 ----> Relay_Ch3

##################################################
# !/usr/bin/python
# -*- coding:utf-8 -*-
import RPi.GPIO as GPIO
import time


class Relees:

    def relayon(self, ch):
        relee = self.Relays[ch - 1]
        GPIO.output(relee, GPIO.HIGH)
        #print('Enciendo rele ' + str(ch))


    def relayoff(self, ch):
        relee = self.Relays[ch - 1]
        GPIO.output(relee, GPIO.LOW)
        #print('Apago rele ' + str(ch))

    def abrir_bomba(self,zona):
        if zona == 1:
            self.relayon(3)

        elif zona == 2:
            self.relayon(6)

        elif zona == 3:
            self.relayon(7)

    def cerrar_bomba(self,zona):
        if zona == 1:
            self.relayoff(3)

        elif zona == 2:
            self.relayoff(6)

        elif zona == 3:
            self.relayoff(7)
    def abrir_zona(self,zona):
        if zona == 1:
            self.relayoff(2)
            self.relayon(1)

        elif zona == 2:
            self.relayoff(5)
            self.relayon(4)

    def cerrar_zona(self,zona):
        if zona == 1:
            self.relayoff(1)
            self.relayon(2)

        elif zona == 2:
            self.relayoff(4)
            self.relayon(5)

    def parar_zona(self,zona):
        if zona == 1:
            self.relayoff(1)
            self.relayoff(2)

        elif zona == 2:
            self.relayoff(4)
            self.relayoff(5)






    def seguridad(self):
        GPIO.output(self.Relay_Ch1, GPIO.LOW)
        GPIO.output(self.Relay_Ch2, GPIO.HIGH)
        GPIO.output(self.Relay_Ch3, GPIO.LOW)
        GPIO.output(self.Relay_Ch4, GPIO.LOW)
        GPIO.output(self.Relay_Ch5, GPIO.HIGH)
        GPIO.output(self.Relay_Ch6, GPIO.LOW)
        GPIO.output(self.Relay_Ch7, GPIO.LOW)
        GPIO.output(self.Relay_Ch8, GPIO.LOW)

    def __init__(self):
        self.Relay_Ch1 = 12
        self.Relay_Ch2 = 5
        self.Relay_Ch3 = 2
        self.Relay_Ch4 = 25
        self.Relay_Ch5 = 24
        self.Relay_Ch6 = 3
        self.Relay_Ch7 = 14
        self.Relay_Ch8 = 4
        self.Relays = [self.Relay_Ch1, self.Relay_Ch2, self.Relay_Ch3, self.Relay_Ch4, self.Relay_Ch5, self.Relay_Ch6, self.Relay_Ch7, self.Relay_Ch8]

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.Relay_Ch1, GPIO.OUT)
        GPIO.setup(self.Relay_Ch2, GPIO.OUT)
        GPIO.setup(self.Relay_Ch3, GPIO.OUT)
        GPIO.setup(self.Relay_Ch4, GPIO.OUT)
        GPIO.setup(self.Relay_Ch5, GPIO.OUT)
        GPIO.setup(self.Relay_Ch6, GPIO.OUT)
        GPIO.setup(self.Relay_Ch7, GPIO.OUT)
        GPIO.setup(self.Relay_Ch8, GPIO.OUT)

        GPIO.output(self.Relay_Ch1, GPIO.LOW)
        GPIO.output(self.Relay_Ch2, GPIO.LOW)
        GPIO.output(self.Relay_Ch3, GPIO.LOW)
        GPIO.output(self.Relay_Ch4, GPIO.LOW)
        GPIO.output(self.Relay_Ch5, GPIO.LOW)
        GPIO.output(self.Relay_Ch6, GPIO.LOW)
        GPIO.output(self.Relay_Ch7, GPIO.LOW)
        GPIO.output(self.Relay_Ch8, GPIO.LOW)

    def test(self):
        try:
            while True:
                for i in range(2):
                    for j in range(4):
                        GPIO.output(self.Relays[i], GPIO.HIGH)
                        print("Channel " + str(i) + ":Abriendo!\n")
                        time.sleep(0.5)

                        GPIO.output(self.Relays[i], GPIO.LOW)
                        print("Channel " + str(i) + ":Cerrando!\n")
                        time.sleep(0.5)




        except:
            print("except")
            GPIO.cleanup()

if __name__ == '__main__':
    rel =Relees()
    rel.test()