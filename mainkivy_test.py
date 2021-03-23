from datetime import datetime
import threading
import time

from UliEngineering.Physics.RTD import pt1000_temperature
import kivy
import json

from kivy.properties import NumericProperty, StringProperty, ObjectProperty
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, FadeTransition, NoTransition

from kivy.uix.textinput import TextInput
import numpy as np

kivy.require("1.9.1")
from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'systemanddock')
Config.set("graphics", "width", "650")
Config.set("graphics", "height", "390")
Config.write()
from LogicaTest import LogicaZona
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder

# Software SPI configuration:
CLK = 18
MISO = 23
MOSI = 24
CS = 25



class Main(ScreenManager):

    def cambia_from(self, num):
        des = self.ids.desde.text
        desde = int(des) + num
        if desde <= 23 and desde >= 0:
            self.ids.desde.text = str(desde)

    def cambia_to(self, num):
        has = self.ids.hasta.text
        hasta = int(has) + num
        if hasta != 24 and hasta != 1:
            self.ids.hasta.text = str(hasta)

    def cambiar_consigna(self, num, zona):
        if zona == 1:
            consigna = self.ids.consigna1.text
        else:
            consigna = self.ids.consigna2.text

        cons_sp1 = consigna.split(']')
        cons_sp2 = cons_sp1[1].split('[')
        consigna = int(cons_sp2[0]) + num
        text = cons_sp1[0] + ']' + str(consigna) + '[' + cons_sp2[1] + ']'

        if zona == 1:
            self.ids.consigna1.text = text
        else:
            self.ids.consigna2.text = text

    def dummy(self):
        pass


def from_level_to_temp(level):
    volt = level * 3.3 / 1024
    r1 = (1000 * volt) / (3.3 - volt)
    temp = pt1000_temperature(r1)
    return temp


class MainApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.img_cnx = "data/nointernet.png"
        self.scheduler = np.zeros((7, 24), dtype=bool)
        self.dict_dias = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3, "Viernes": 4, "Sabado": 5, "Domingo": 6,
                          "Lectivos": [0, 1, 2, 3, 4], "Finde": [5, 6], "Todos": [0, 1, 2, 3, 4, 5, 6], }
        self.t_ext = 35
        self.act_screen = "menu"
        self.chanels = np.zeros(8)

        self.t_amb = [20, 20, 20]

        self.t_suelo = [25, 25]

        self.t_agua = [25, 25]

        self.modo = "invierno"

        self.consignas = [20, 20, 20]

        self.reducido_inv = [19, 19]
        self.reducido_ver = [26, 26]

        self.apagado_inv = [10, 10]
        self.apagado_ver = [35, 35]

        self.bombas = [False, False]
        self.curvas = [0, 0]

        self.comfort = [0, 0]

        self.states = {"winter": "down", "summer": "normal", "noice": "normal"}

        self.ajustes = True
        self.pt1000 = True
        self.logicas = [LogicaZona(1), LogicaZona(2), LogicaZona(3)]

        self.mutex = threading.Semaphore(1)
        thread1 = threading.Thread(target=self.main, args=[1])
        thread1.start()
        thread2 = threading.Thread(target=self.main, args=[2])
        thread2.start()

    def borrar_scheduler(self):
        self.scheduler[:, :] = False
        print(self.scheduler)

    def set_scheduler(self):
        dias = self.root.ids.dias.text
        desde = int(self.root.ids.desde.text)
        hasta = int(self.root.ids.hasta.text)
        if desde < hasta and dias != "Dias":
            self.scheduler[self.dict_dias[dias], desde:hasta] = True
            print(self.scheduler)
            self.root.ids.sched_err.text = ""
        else:
            self.root.ids.sched_err.text = "Error"

    def cambiar_cons_reducido(self, num, zona, modo):
        zona = zona - 1
        if zona == 0:
            if modo == 'inv':
                self.reducido_inv[zona] = self.reducido_inv[zona] + num
                self.root.ids.cons_z1_inv_red.text = str(self.reducido_inv[zona])
            else:
                self.reducido_ver[zona] = self.reducido_ver[zona] + num
                self.root.ids.cons_z1_ver_red.text = str(self.reducido_ver[zona])
        elif zona == 1:
            if modo == 'inv':
                self.reducido_inv[zona] = self.reducido_inv[zona] + num
                self.root.ids.cons_z2_inv_red.text = str(self.reducido_inv[zona])

            else:
                self.reducido_ver[zona] = self.reducido_ver[zona] + num
                self.root.ids.cons_z2_ver_red.text = str(self.reducido_ver[zona])

    def cambiar_cons_apagado(self, num, zona, modo):
        zona = zona - 1
        if zona == 0:
            if modo == 'inv':
                self.apagado_inv[zona] = self.apagado_inv[zona] + num
                self.root.ids.cons_z1_inv_apa.text = str(self.apagado_inv[zona])
            else:
                self.apagado_ver[zona] = self.apagado_ver[zona] + num
                self.root.ids.cons_z1_ver_apa.text = str(self.apagado_ver[zona])
        elif zona == 1:
            if modo == 'inv':
                self.apagado_inv[zona] = self.apagado_inv[zona] + num
                self.root.ids.cons_z2_inv_apa.text = str(self.apagado_inv[zona])

            else:
                self.apagado_ver[zona] = self.apagado_ver[zona] + num
                self.root.ids.cons_z2_ver_apa.text = str(self.apagado_ver[zona])

    def next(self,filename):
        filename = 'kv/' + filename + '.kv'
        self.root.ids.sm.clear_widgets()

    def cambiar_modo(self, modo):
        self.modo = modo
        if modo == 'invierno':
            self.states['winter'] = 'down'
            self.states['summer'] = 'normal'
            self.states['noice'] = 'normal'
            color = '[color=00E4FF]'
        if modo == 'verano':
            self.states['winter'] = 'normal'
            self.states['summer'] = 'down'
            self.states['noice'] = 'normal'
            color = '[color=FF8700]'
        if modo == 'antihielo':
            self.states['winter'] = 'normal'
            self.states['summer'] = 'normal'
            self.states['noice'] = 'down'
            color = '[color=EF4A4A]'

        self.root.ids.modo1.text = color + modo.capitalize() + '[/color]'
        self.root.ids.modo2.text = color + modo.capitalize() + '[/color]'
        self.root.ids.modo3.text = color + modo.capitalize() + '[/color]'

    def modo_comfort(self, comfort, zona):
        self.comfort[zona] = comfort

    def modo_curva(self, curva, zona):
        self.curvas[zona] = curva

    def modo_bomba(self, zona, modo):
        self.bombas[zona] = modo

    def lock(self):
        self.ajustes = True
        self.next_screen('menu')

    def do_login(self, user, password):
        with open("json_f/user.json") as f:
            login = json.load(f)

        print(user, password)
        if user == login['user'] and password == login['password']:
            print("Loged")
            self.root.current = "ajustes_admin"

        else:
            self.root.ids.user.text = ''
            self.root.ids.passw.text = ''

    def lectura_sondas(self):
        while True:
            self.t_ext = self.chanels[0]
            self.t_suelo[0] = self.chanels[1]
            self.t_agua[0] = self.chanels[2]
            self.t_amb[0] = self.chanels[3]

            self.root.ids.t_ext.text = str(self.t_ext)
            self.root.ids.t_amb.text = str(self.t_amb[0])
            self.root.ids.t_agua.text = str(self.t_agua[0])
            self.root.ids.t_suelo.text = str(self.t_suelo[0])

            self.root.ids.t_exterior.text = str(self.t_ext)
            self.root.ids.t_amb_z1.text = str(self.t_amb[0])
            self.root.ids.t_agua_z1.text = str(self.t_agua[0])
            self.root.ids.t_suelo_z1.text = str(self.t_suelo[0])

            self.root.ids.t_amb_z2.text = str(self.t_amb[1])
            self.root.ids.t_agua_z2.text = str(self.t_agua[1])
            self.root.ids.t_suelo_z2.text = str(self.t_suelo[1])
            time.sleep(1)

    def main(self, zona):
        zona = zona - 1
        while True:
            try:

                while True:
                    ahora = datetime.now()
                    hora = ahora.hour
                    dia = datetime.weekday(ahora)
                    sched = self.scheduler[dia, hora]

                    self.mutex.acquire()
                    self.logicas[zona].sonda_exterior = self.t_ext
                    self.logicas[zona].sonda_ambiente = self.t_amb[zona]
                    self.logicas[zona].sonda_agua = self.t_agua[zona]
                    self.logicas[zona].sonda_suelo = self.t_suelo[zona]
                    self.logicas[zona].modo_bomba = self.bombas[zona]
                    self.logicas[zona].modo_curva = self.curvas[zona]
                    self.logicas[zona].grado_confort = self.comfort[zona]

                    self.logicas[zona].consigna = self.consignas[zona]

                    self.mutex.release()

                    func = self.logicas[zona].logica(self.modo)

            finally:
                print("Error")
    def cambiar_titulos(self,zona):
        if zona == 1 :
            self.root.ids.title_1.text = self.root.ids.new_title1.text
            self.root.ids.new_title1.text = ''
        elif zona == 2 :
            self.root.ids.title_2.text = self.root.ids.new_title2.text
            self.root.ids.new_title2.text = ''
        elif zona == 3 :
            self.root.ids.title_3.text = self.root.ids.new_title3.text
            self.root.ids.new_title2.text = ''

    def cambiar_consigna(self, num, zona):
        self.consignas[zona] = self.consignas[zona] + num
        if zona == 0:
            self.root.ids.cons_z1_inv_conf.text = str(self.consignas[zona])
            self.root.ids.cons_z1_ver_conf.text = str(self.consignas[zona])
        elif zona == 1:
            self.root.ids.cons_z2_inv_conf.text = str(self.consignas[zona])
            self.root.ids.cons_z2_ver_conf.text = str(self.consignas[zona])

        else:
            self.root.ids.consigna3.text = '[color=1ED760]' + str(self.consignas[zona]) + '[/color]'

    def next_screen(self, screen):
        self.act_screen = screen
        filename = screen + '.kv'
        Builder.unload_file('kv/' + filename)

        self.root.container.clear_widgets()
        screen = Builder.load_file('kv/' + filename)
        # add the content of the .kv file to the container
        self.root.container.add_widget(screen)

    def build(self):
        self.root = Builder.load_file('kv/main.kv')

    def act_values(self):
        pass


if __name__ == '__main__':
    MainApp().run()
