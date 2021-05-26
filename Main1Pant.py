from datetime import datetime
import threading
import time
from socket import create_connection, gethostbyname, error
from UliEngineering.Physics.RTD import pt1000_temperature
import kivy
import json
import os
from kivy.uix.screenmanager import ScreenManager

import numpy as np
import math

kivy.require("1.9.1")
from kivy.config import Config

Config.set('kivy', 'keyboard_mode', 'systemanddock')

Config.set("graphics", "width", "650")
Config.set("graphics", "height", "390")
Config.set("graphics", "show_cursor", 0)
Config.write()
from LogicaUna import LogicaZona, LogicaZonaDirecta
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock, mainthread
import calendar

#import Adafruit_DHT
from MCP3208 import MCP3208
# Software SPI configuration:
import time
import random
import socket
import sys
import selectors
import types
import logging
import configparser

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filename='asigeo.log', filemode='w+', level=logging.INFO)
# Software SPI configuration:
CLK = 11
MISO = 9
MOSI = 10
CS = 8

sem = threading.Semaphore()
sem1 = threading.Semaphore()
sem2 = threading.Semaphore()
semTelemetry = threading.Semaphore()
semScheduler = threading.Semaphore()
semModo = threading.Semaphore()
semConsignas = threading.Semaphore()

mcp = MCP3208(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)


config = configparser.ConfigParser()
config.read('/home/pi/ASIGEO/settings.ini')


IPCLIENT=config['NET']['ipclient']


class Client:

	hostname=0
	servers=[]
	n_servers=0
	socks=[]
	asincrono_ = 1
	sel = selectors.DefaultSelector()

	def __init__(self, h=0):
		self.hostname = h

	def asincrono(self):
		self.asincrono_ = 0

	def sincrono(self):
		self.asincrono_ = 1

	def isAsincrono(self):
		return self.asincrono_ == 0

	def getServer(self, hostname):
		i = 0
		for server in self.servers:
			if server == hostname:
				return i
			i = i + 1
	
		return -1

	def connect(self,host,port, data=None):
		sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		if self.asincrono_==0:
			sock.setblocking(False)
		self.socks = [sock] + self.socks
		self.socks[0].connect_ex((host,port))
		self.n_servers = self.n_servers + 1
		self.servers=[host] + self.servers
		if self.asincrono_ ==0:
			self.sel.register(self.socks[0], events, data)

		

	def sendMsg(self,msg,server):			   
		return self.socks[self.getServer(server)].send(msg)

	def sendAllServers(self,msg):
		for sock in self.socks:
			self.sock.send(msg)

	def receiveMsg(self,server):
		return self.socks[self.getServer(server)].recv(1024)

	def getServers(self):
		return self.servers

	def setSevers(self, list_servers):
		for server in list_servers:
			self.servers = [server] + self.servers
			self.n_servers = self.n_servers + 1

	def getNumberServers(self):
		return self.n_servers

	def setHostname(self, host):
		self.hostname = host

	def getHostname(self):
		return self.hostname

	def disconnectFromServer(self):
		for client in self.socks:
			client.close()

	def getSelector(self):
		return self.sel.select(timeout=None)

	def unregisterSock(self, sock):
		self.sel.unregister(self.socks[0])


events = selectors.EVENT_READ | selectors.EVENT_WRITE
telemetry = []
flag_cambiado=[[0,0],[0,0],[0,0],[0,0]]

def createSubJSON(tSuelo, tAmbiente, tAgua, zona):
	jsonValue1='\"tsuelo' + str(zona) +'\":' + str(tSuelo) + ','
	jsonValue1=jsonValue1+'\"tambiente' + str(zona) +'\":' + str(tAmbiente) + ','
	jsonValue1=jsonValue1+'\"tagua' + str(zona) +'\":' + str(tAgua)
	return jsonValue1

def createJSON(temperaturas):
	jsonValue1= createSubJSON(temperaturas[0][0], temperaturas[0][1], temperaturas[0][2],1)
	jsonValue2= createSubJSON(temperaturas[1][0], temperaturas[1][1], temperaturas[1][2],2)
	jsonValue3='\"tambiente3\":' + str(temperaturas[2][0])
	s='{'+jsonValue1 + ','
	s=s+ jsonValue2 + ','
	s=s+jsonValue3 + ','
	s=s+'\"texterior\":' + str(temperaturas[3][0]) + '}\n'
	return s


def checkFirstConnection(client, host, app, firstconnection):
	if firstconnection:
		firstconnection = False
		semConsignas.acquire()
		semModo.acquire()
		state = '{\"modo\":' + '\"' + app.modo + '\"' + ',' + '\"consignaZona1\":' + str(app.consignas[0]) + ',' + '\"consignaZona2\":' + str(app.consignas[1]) + ',' + '\"consignaZona3\":' + str(app.consignas[2]) +',\"nZonas\":' + str(3) + '}\n'
		semConsignas.release()
		semModo.release()
		msg=state.encode("utf-8")
		print('Client sending', repr(msg), 'to connection', 0)
		sent = client.sendMsg(msg, host)  # Should be ready to write
		msg = ''
		return firstconnection


def rutinaRecepcion(client, host, app, data):
	recv_data = client.receiveMsg(host)  # Should be ready to read
	print(client.getHostname(),' recibido del server ', repr(recv_data))
	recv_data = recv_data.decode("utf-8").split("\n")
	print(client.getHostname(),' recibido del server ', repr(recv_data))
	if(len(recv_data)>1):
		recv_data = recv_data[0:len(recv_data)-1]
	print(client.getHostname(),' recibido del server ', repr(recv_data))
	while recv_data:
		if recv_data[0] and recv_data[0]!='ack':
			print('Client received', repr(recv_data[0]), 'from connection', 0)
			info = json.loads(recv_data[0])
			if "modo" in info:
				print("Cambiando modo")
				app.cambiar_modo(info["modo"], 0)
			if "consignaZona1" in info:
				print("Cambiando consigna")
				app.root.cambiar_consigna(int(info["consignaZona1"]), 1)
				app.cambiar_consigna(int(info["consignaZona1"]), 0, 0)
			if "consignaZona2" in info:
				print("Cambiando consigna")
				app.root.cambiar_consigna(int(info["consignaZona2"]), 2)
				app.cambiar_consigna(int(info["consignaZona2"]), 1, 0)
			if "consignaZona3" in info:
				print("Cambiando consigna")
				app.root.cambiar_consigna(int(info["consignaZona3"]), 3)
				app.cambiar_consigna(int(info["consignaZona3"]), 2, 0)
			data.outb = [b'ack\n'] + data.outb
			recv_data = recv_data[1:]
		elif recv_data[0]:
			print('Client received ', recv_data)
			recv_data = recv_data[1:]
	return data

def rutinaEnvio(client, host, app, data):
	global telemetry
	aux =[]
	if flag_cambiado[0][0]==1 and calendar.timegm(time.gmtime())-flag_cambiado[0][1]>=10:
		logging.info("Cambio realizado por usuario notificando TB")
		semModo.acquire()
		s = '{\"modo\":' + '\"' + app.modo + '\"' + '}\n'
		flag_cambiado[0][0]=0
		semModo.release()
		aux = [s.encode('utf-8')]
	if flag_cambiado[1][0]==1 and calendar.timegm(time.gmtime())-flag_cambiado[1][1]>=10:
		logging.info("Cambio realizado por usuario notificando TB")
		semConsignas.acquire()
		s = '{\"consignaZona1\":' + str(app.consignas[0]) +'}\n'
		flag_cambiado[1][0]=0
		semConsignas.release()
		aux = [s.encode('utf-8')]
	if flag_cambiado[2][0]==1 and calendar.timegm(time.gmtime())-flag_cambiado[2][1]>=10:
		logging.info("Cambio realizado por usuario notificando TB")
		semConsignas.acquire()
		s = '{\"consignaZona2\":' + str(app.consignas[1]) +'}\n'
		flag_cambiado[2][0]=0
		semConsignas.release()
		aux = [s.encode('utf-8')]
	if flag_cambiado[3][0]==1 and calendar.timegm(time.gmtime())-flag_cambiado[3][1]>=10:
		logging.info("Cambio realizado por usuario notificando TB")
		semConsignas.acquire()
		s = '{\"consignaZona3\":' + str(app.consignas[2]) + '}\n'
		flag_cambiado[3][0]=0
		semConsignas.release()
		aux = [s.encode('utf-8')]
	sem1.acquire()
	telemetry = aux + telemetry
	data.messages =telemetry
	sem1.release()
	if not data.outb and data.messages:
		data.outb = data.outb+[data.messages.pop(0)]
	if data.outb:
		print('Client sending', repr(data.outb[0]), 'to connection', 0)
		sent = client.sendMsg(data.outb[0], host)  # Should be ready to write
		data.outb[0] = data.outb[0][sent+1:]
		if len(data.outb[0])==0:
			data.outb = data.outb[1:]
	return data


def service_connectionClient(key, mask, client, host, app, firstconnection):
	sock = key.fileobj
	data = key.data
	firstconnection=checkFirstConnection(client, host, app, firstconnection)
	if mask & selectors.EVENT_READ:
		data = rutinaRecepcion(client, host, app, data)
	if mask & selectors.EVENT_WRITE:
		data = rutinaEnvio(client, host, app, data)
	return firstconnection

def DemoClient(port, host, app):
	time.sleep(60)
	client = Client(IPCLIENT)
	server_addr = (host, port)
	print('Client starting connection', 0, 'to', server_addr)
	client.asincrono()
	data = types.SimpleNamespace(addr=server_addr, connid=0,
					 msg_total=sum(len(m) for m in telemetry),
					 recv_total=0,
					 messages=list(telemetry),
					 outb=[])
	client.connect(host, port, data=data)
	firstconnection = True
	while True:
		events = client.getSelector()
		for key, mask in events:
			time.sleep(2)
			firstconnection = service_connectionClient(key, mask, client, host, app, firstconnection)


def comprobarConexion():
	try:
		gethostbyname('google.com')
		cnx = create_connection(('google.com', 80), 1)
		conexion = True
	except:
		conexion = False

	return conexion


class Main(ScreenManager):
	def dummy(self):
		pass

	def cambia_from(self, num):
		des = self.ids.desde.text
		desde = int(des) + num
		if 23 >= desde >= 0:
			self.ids.desde.text = str(desde)

	def cambia_to(self, num):
		has = self.ids.hasta.text
		hasta = int(has) + num
		if hasta != 24 and hasta != 1:
			self.ids.hasta.text = str(hasta)

	def cambiar_consigna(self, num, zona):
		sem2.acquire()
		if zona == 1:
			consigna = self.ids.consigna1.text
		elif zona == 2:
			consigna = self.ids.consigna2.text

		else:
			consigna = self.ids.consigna3.text
		logging.info("Cambiando consigna: " + str(consigna) + "de la zona: "+ str(zona))
		consigna = int(consigna)
		if num < 10 and num!=1 and (num==-1 and consigna+num<10):
			consigna = consigna
		elif num == 1 or (num==-1 and consigna+num>=10):
			consigna = consigna + num
		else:
			consigna = num
		text = str(consigna)
		logging.info("Cambiando consigna: " + text + "de la zona: "+ str(zona))

		if zona == 1:
			self.ids.consigna1.text = text
		elif zona == 2:
			self.ids.consigna2.text = text
		else:
			self.ids.consigna3.text = text
		sem2.release()


def from_level_to_temp(level):
	error = False
	volt = level * 3.15 / 4200
	r = (1000 * volt) / (3.15 - volt)
	r1 = 100000 * r / (100000 - r)
	temp = pt1000_temperature(r1)
	if np.isnan(temp) or -100 < temp > 100:
		error = True
	return temp, error


def from_level_to_temp_ntc(beta, r25, level):
	volt = level * 3.15 / 4200
	r = (10000 * volt) / (3.15 - volt)
	r1 = 100000 * r / (100000 - r)
	error = False
	temp = -30
	if r1 > 0:
		temp = beta / (math.log(r1 / r25) + beta / 298) - 273
	else:
		error = True

	if temp < -17:
		error = True
	return temp, error


class MainApp(App):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		# SEGURIDADES
		logging.info("Primero")
		with open('/home/pi/ASIGEO/json_f/seguridades.json', 'r') as file:
			seguridades = json.load(file)

		self.act_seguridades = 0



		self.dict_dias = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3, "Viernes": 4, "Sabado": 5, "Domingo": 6,
						  "Laborables": [0, 1, 2, 3, 4], "Fin de semana": [5, 6], "Todos": [0, 1, 2, 3, 4, 5, 6], }
		self.colores = {0: [0.99, .0, .0], 1: [1, .82, .0], 2: [.0, 1., 0.62]}
		self.t_ext = 35
		self.act_screen = "menu"
		self.chanels = [0, 0, 0, 0, 0, 0, 0, 0]
		self.ch_errors = [False, False, False, False, False, False, False, False]
		self.error = False
		self.t_amb = [20, 20, 20]
		self.etiqprinc = ""
		self.t_suelo = [25, 25]

		self.t_agua = [25, 25]
		self.scheduler = np.load("/home/pi/ASIGEO/json_f/scheduler.npy")
		with open("/home/pi/ASIGEO/json_f/modo.json") as f:
			modo = json.load(f)
			self.modo = modo['modo']
			logging.info("El modo con el que se ha inicializado es " + self.modo)
		if self.modo == "invierno":
			self.etiqprinc = '[b][color=FF1700] MODO CALEFACCION [/color][/b]'

		elif self.modo == "verano":
			self.etiqprinc = '[b][color=5FE5B5] MODO REFRIGERACION [/color][/b]'

		else:
			self.etiqprinc = '[b][color=A49B0F] MODO ANTIHIELO [/color][/b]'

		with open("/home/pi/ASIGEO/json_f/pantalla1.json") as f:
			pant = json.load(f)
			cons1 = pant['consigna']

		with open("/home/pi/ASIGEO/json_f/pantalla2.json") as f:
			pant = json.load(f)
			cons2 = pant['consigna']

		with open("/home/pi/ASIGEO/json_f/pantalla3.json") as f:
			pant = json.load(f)
			cons3 = pant['consigna']
		self.consignas = [cons1, cons2, cons3]
		with open("/home/pi/ASIGEO/json_f/consignas.json") as f:
			pant = json.load(f)
			self.reducido_inv = pant['reducido_inv']
			self.reducido_ver = pant['reducido_ver']
			self.apagado_inv = pant['apagado_inv']
			self.apagado_ver = pant['apagado_ver']

		self.zona = 0


		with open("/home/pi/ASIGEO/json_f/ajustes.json") as f:
			ajustes = json.load(f)
			bombas = ajustes['bombas']
			self.bombas = [bool(bombas[0]), bool(bombas[1])]
			self.curvas = ajustes['curvas']
			self.pt1000 = ajustes['pt1000']

		self.comfort = [0, 0]
		with open("/home/pi/ASIGEO/json_f/states.json") as f:
			self.states = json.load(f)
		with open("/home/pi/ASIGEO/json_f/states_sondas.json") as f:
			self.states_sondas = json.load(f)

		with open("/home/pi/ASIGEO/json_f/estado_bombas.json") as f:
			self.estado_bombas = json.load(f)
		with open("/home/pi/ASIGEO/json_f/estado_curvas.json") as f:
			self.estado_curvas = json.load(f)

		self.ajustes = True

		self.logicas = [LogicaZona(1), LogicaZona(2)]
		self.zona_directa = LogicaZonaDirecta(rele=7)

		thread1 = threading.Thread(target=main, args=[self, 1])
		thread1.start()

		thread2 = threading.Thread(target=main, args=[self, 2])
		thread2.start()

		thread3 = threading.Thread(target=main_directa, args=[self, 3])
		thread3.start()

		th_read = threading.Thread(target=lectura_sondas, args=[self])
		th_read.start()

		th_read2 = threading.Thread(target=DemoClient, args=[51412, '127.0.0.3', self])
		th_read2.start()



	def backzone(self):
		if self.zona == 0:
			self.root.current = "menu1"
		elif self.zona == 1:
			self.root.current = "menu2"
	def camzona(self,zona):
		self.zona = zona

	def getConsignas(self, zona, s):
		semConsignas.acquire()
		if zona == 1:
			if s == "inv_conf":
				yield self.consignas[zona-1]
			elif s == "ver_conf":
				yield self.consignas[zona-1]
			elif s == "inv_apa":
				yield self.apagado_inv[zona-1]
			elif s == "inv_red":
				yield self.reducido_inv[zona-1]
			elif s == "ver_apa":
				yield self.apagado_ver[zona-1]
			elif s == "ver_red":
				yield self.reducido_ver[zona-1]

		elif zona== 2:
			if s == "inv_conf":
				yield  self.consignas[zona-1]
			elif s == "ver_conf":
				yield self.consignas[zona-1]
			elif s == "inv_apa":
				yield self.apagado_inv[zona-1]
			elif s == "inv_red":
				yield self.reducido_inv[zona-1]
			elif s == "ver_apa":
				yield self.apagado_ver[zona-1]
			elif s == "ver_red":
				yield self.reducido_ver[zona-1]
		elif zona==3:
			if s == "inv_conf":
				yield  self.consignas[zona-1]
			elif s == "ver_conf":
				yield self.consignas[zona-1]

		semConsignas.release()

	def set_secvalue(self):

		modo = self.root.ids.seg_modo.text
		zona = self.root.ids.seg_zonas.text
		sec = self.root.ids.seguridades.text
		logging.info(modo, zona, sec)
		seguridad = self.get_seguridad(modo, zona, sec)

		logging.info(seguridad)

		with open('/home/pi/ASIGEO/json_f/seguridades.json') as f:
			seguridades = json.load(f)
			self.root.ids.valor_actual.text = str(seguridades[seguridad])
			self.root.ids.nuevo_valor.text = ''

	def cambiar_titulos(self, zona):
		if zona == 1:
			self.root.ids.title_1.text = self.root.ids.new_title1.text
			self.root.ids.new_title1.text = ''
		elif zona == 2:
			self.root.ids.title_2.text = self.root.ids.new_title2.text
			self.root.ids.new_title2.text = ''
		elif zona == 3:
			self.root.ids.title_3.text = self.root.ids.new_title3.text
			self.root.ids.new_title3.text = ''

	def rm_label(self):
		self.root.ids.valor_actual.text = ''
		self.root.ids.nuevo_valor.text = ''

	def reset_fabrica(self):
		os.system('sh reset_parametros.sh')

	def set_seguridad(self):
		modo = self.root.ids.seg_modo.text
		zona = self.root.ids.seg_zonas.text
		sec = self.root.ids.seguridades.text
		n_valor = self.root.ids.nuevo_valor.text
		try:
			nvalor = int(n_valor)
			seguridad = self.get_seguridad(modo, zona, sec)
			logging.info(seguridad)
			with open('/home/pi/ASIGEO/json_f/seguridades.json', 'r+') as f:
				seguridades = json.load(f)
			with open('/home/pi/ASIGEO/json_f/seguridades.json', 'w') as f:

				if seguridad != 0:
					f.seek(0)
					self.root.ids.valor_actual.text = str(nvalor)
					seguridades[seguridad] = nvalor
					json.dump(seguridades, f, indent=4)
					self.root.ids.sec_err.text = ""
				else:
					self.root.ids.sec_err.text = "Seguridad no seleccionada"


		except:
			self.root.ids.sec_err.text = "Valores numéricos erroneos"

	def get_seguridad(self, modo, zona, sec):
		if modo == 'Verano':
			pre = 'ver'
		elif modo == 'Invierno':
			pre = 'inv'
		elif modo == 'Antihielo':
			pre = 'ant'

		if sec == 'T min Suelo':
			mid = '_tmin_suelo'
		elif sec == 'T max Suelo':
			mid = '_tmax_suelo'
		elif sec == 'T min Agua':
			mid = '_tmin_agua'
		elif sec == 'T max Agua':
			mid = '_tmax_agua'
		elif sec == 'T min Exterior':
			seguridad = pre + '_tmin_ext'
		else:
			return 0

		if zona != 'Comunes':
			pos = zona[-1]
			seguridad = pre + mid + pos

		return seguridad

	def readSensors(self):
		logging.info('Leyendo sensores')
		error = False
		for i in range(0, 8):
			lev = mcp.read(i)

			if self.pt1000[i]:
				ch, err = from_level_to_temp(lev)
			else:
				if i == 3 or i == 6:
					ch, err = from_level_to_temp_ntc(3976, 10000, lev)
				else:
					ch, err = from_level_to_temp_ntc(3435, 10000, lev)

			if err:
				self.ch_errors[i] = True
				error = True
			else:
				self.ch_errors[i] = False

			self.chanels[i] = ch
		self.error = error

		logging.info(self.chanels)

	def borrar_scheduler(self):
		semScheduler.acquire()
		self.scheduler[:, :, :] = 0
		np.save("/home/pi/ASIGEO/json_f/scheduler.npy",self.scheduler)
		semScheduler.release()

	def cambiar_modo(self, modo, flag_user):
		sem.acquire()
		semModo.acquire()
		self.modo = modo
		global flag_cambiado
		if flag_user==1:
			flag_cambiado[0][0]=1
			flag_cambiado[0][1]=calendar.timegm(time.gmtime())
		semModo.release()
		if modo == 'invierno':
			self.states['winter'] = 'down'
			self.states['summer'] = 'normal'
			self.states['noice'] = 'normal'
			color = '[color=00E4FF]'
			self.root.ids.modo0.text = '[b][color=FF1700] MODO CALEFACCION [/color][/b]'
		if modo == 'verano':
			self.states['winter'] = 'normal'
			self.states['summer'] = 'down'
			self.states['noice'] = 'normal'
			color = '[color=FF8700]'
			self.root.ids.modo0.text = '[b][color=54EDE1] MODO REFRIGERACION [/color][/b]'
		if modo == 'antihielo':
			self.states['winter'] = 'normal'
			self.states['summer'] = 'normal'
			self.states['noice'] = 'down'
			color = '[color=EF4A4A]'
			self.root.ids.modo0.text = '[b][color=F1F132] MODO ANTIHIELO [/color][/b]'

		self.root.ids.modo1.text = color + modo.capitalize() + '[/color]'
		self.root.ids.modo2.text = color + modo.capitalize() + '[/color]'
		self.root.ids.modo3.text = color + modo.capitalize() + '[/color]'
		semModo.acquire()
		data = {
			'modo': self.modo
		}
		semModo.release()
		with open('/home/pi/ASIGEO/json_f/modo.json', 'w') as file:
			json.dump(data, file, indent=4)

		with open('/home/pi/ASIGEO/json_f/states.json', 'w') as file:
			json.dump(self.states, file,indent=4)
		sem.release()

	def getModo(self):
		semModo.acquire()
		yield self.modo.capitalize()
		semModo.release()


	def modo_comfort(self, comfort, zona):
		self.comfort[zona] = comfort

	def copiar_sched(self):
		dia = self.root.ids.dias.text
		dia = self.dict_dias[dia]
		zona = self.zona
		dia_copiar = self.root.ids.copiar_a.text
		if dia_copiar!="-":
			dia_copiar = self.dict_dias[dia_copiar]
			semScheduler.acquire()
			dia_sched = self.scheduler[zona, dia, :]
			self.scheduler[zona, dia_copiar, :] = dia_sched
			np.save("/home/pi/ASIGEO/json_f/scheduler.npy", self.scheduler)
			semScheduler.release()

	def reset_sched(self):
		semScheduler.acquire()
		self.scheduler = np.zeros((2, 7, 24))
		self.root.ids.dias.text = 'Lunes'
		self.cambiar_dia()
		np.save("/home/pi/ASIGEO/json_f/scheduler.npy", self.scheduler)
		semScheduler.release()

	def cambiar_dia(self):
		dia = self.root.ids.dias.text
		dia = self.dict_dias[dia]
		dia_sched = self.scheduler[self.zona, dia, :]

		h1 = self.colores[int(dia_sched[0])]
		self.root.ids.h00.background_color = self.colores[int(dia_sched[0])]
		self.root.ids.h01.background_color = self.colores[int(dia_sched[1])]
		self.root.ids.h02.background_color = self.colores[int(dia_sched[2])]
		self.root.ids.h03.background_color = self.colores[int(dia_sched[3])]
		self.root.ids.h04.background_color = self.colores[int(dia_sched[4])]
		self.root.ids.h05.background_color = self.colores[int(dia_sched[5])]
		self.root.ids.h06.background_color = self.colores[int(dia_sched[6])]
		self.root.ids.h07.background_color = self.colores[int(dia_sched[7])]
		self.root.ids.h08.background_color = self.colores[int(dia_sched[8])]
		self.root.ids.h09.background_color = self.colores[int(dia_sched[9])]
		self.root.ids.h10.background_color = self.colores[int(dia_sched[10])]
		self.root.ids.h11.background_color = self.colores[int(dia_sched[11])]
		self.root.ids.h12.background_color = self.colores[int(dia_sched[12])]
		self.root.ids.h13.background_color = self.colores[int(dia_sched[13])]
		self.root.ids.h14.background_color = self.colores[int(dia_sched[14])]
		self.root.ids.h15.background_color = self.colores[int(dia_sched[15])]
		self.root.ids.h16.background_color = self.colores[int(dia_sched[16])]
		self.root.ids.h17.background_color = self.colores[int(dia_sched[17])]
		self.root.ids.h18.background_color = self.colores[int(dia_sched[18])]
		self.root.ids.h19.background_color = self.colores[int(dia_sched[19])]
		self.root.ids.h20.background_color = self.colores[int(dia_sched[20])]
		self.root.ids.h21.background_color = self.colores[int(dia_sched[21])]
		self.root.ids.h22.background_color = self.colores[int(dia_sched[22])]
		self.root.ids.h23.background_color = self.colores[int(dia_sched[23])]

	def set_sched_hora(self, hora, dia, valor):
		semScheduler.acquire()
		dia_sched = self.dict_dias[dia]
		self.scheduler[self.zona, dia_sched, hora] = valor
		np.save("/home/pi/ASIGEO/json_f/scheduler.npy", self.scheduler)
		semScheduler.release()

	def dummy(self):
		pass

	def listToString(self, s):  
    
	    # initialize an empty string 
		str1 = " " 
		for ele in s:  
			str1 += ele   
    
	    # return string   
		return str1 

	def modo_curva(self, curva, zona):
		self.curvas[zona] = curva
		with open("/home/pi/ASIGEO/json_f/ajustes.json", 'r+') as f:
			ajustes = json.load(f)
			aj_curva = ajustes['curvas']
			aj_curva[zona] = int(curva)
			ajustes['curvas'] = aj_curva
			f.seek(0)
			json.dump(ajustes, f,indent=4)

		if curva == 0:
			self.estado_curvas[zona]["b1"] = "down"
			self.estado_curvas[zona]["b2"] = "normal"
			self.estado_curvas[zona]["b3"] = "normal"
		elif curva == 1:
			self.estado_curvas[zona]["b1"] = "normal"
			self.estado_curvas[zona]["b2"] = "down"
			self.estado_curvas[zona]["b3"] = "normal"
		elif curva == 2:
			self.estado_curvas[zona]["b1"] = "normal"
			self.estado_curvas[zona]["b2"] = "normal"
			self.estado_curvas[zona]["b3"] = "down"
		with open("/home/pi/ASIGEO/json_f/estado_curvas.json", "w") as f:
			json.dump(self.estado_curvas, f, indent=4)
		#logging.info('JSON curvas: ' + self.listToString(self.estado_curvas))

	def modo_bomba(self, zona, modo):
		self.bombas[zona] = modo
		with open("/home/pi/ASIGEO/json_f/ajustes.json", 'r+') as f:
			ajustes = json.load(f)
			aj_bomba = ajustes['bombas']
			aj_bomba[zona] = int(modo)
			ajustes['bombas'] = aj_bomba
			f.seek(0)
			json.dump(ajustes, f,indent=4)
		if modo:
			self.estado_bombas[zona]["b1"] = "normal"
			self.estado_bombas[zona]["b2"] = "down"
			try:

				if zona==0: self.root.ids.mod_bomb_z1.text = "[b] MODO ECO [/b]"
				elif zona==1: self.root.ids.mod_bomb_z2.text = "[b] MODO ECO [/b]"
			except:
				logging.info(Exception)
		else:
			self.estado_bombas[zona]["b1"] = "down"
			self.estado_bombas[zona]["b2"] = "normal"
			try:

				if zona==0: self.root.ids.mod_bomb_z1.text = "[b] AUTO ON [/b]"
				elif zona==1: self.root.ids.mod_bomb_z2.text = "[b] AUTO ON [/b]"
			except:
				logging.info(Exception)
		with open("/home/pi/ASIGEO/json_f/estado_bombas.json", "w") as f:
			json.dump(self.estado_bombas, f, indent=4)
			#logging.info('JSON bombas: ' + self.listToString(self.estado_bombas))


	def cambia_sonda(self, sonda, num):
		self.pt1000[num] = sonda
		with open("/home/pi/ASIGEO/json_f/ajustes.json", 'r+') as f:
			ajustes = json.load(f)
			ajustes['pt1000'] = self.pt1000
			f.seek(0)
			json.dump(ajustes, f,indent=4)

		if sonda == 0:
			self.states_sondas[num]["b1"] = "normal"
			self.states_sondas[num]["b2"] = "down"
		else:
			self.states_sondas[num]["b1"] = "down"
			self.states_sondas[num]["b2"] = "normal"
		with open("/home/pi/ASIGEO/json_f/states_sondas.json", "w") as f:
			json.dump(self.states_sondas, f, indent=4)
	def lock(self):
		self.ajustes = True
		self.next_screen('menu')

	def do_login(self, user, password):
		with open("/home/pi/ASIGEO/json_f/user.json") as f:
			login = json.load(f)
		if user == login['user'] and password == login['password']:
			self.root.current = "ajustes_admin"
			self.root.ids.user.text = ''
			self.root.ids.passw.text = ''

		else:
			self.root.ids.user.text = ''
			self.root.ids.passw.text = ''

	def valoresSensores(self, s, zona):
		semTelemetry.acquire()
		if s == 't_ext':
			yield self.t_ext
		elif s == 't_amb' and zona == 1:
			yield self.t_amb[0]
		elif s == 't_suelo' and zona == 1:
			yield self.t_suelo[0]
		elif s == 't_agua' and zona == 1:
			yield self.t_agua[0]
		elif s == 't_amb' and zona == 2:
			yield self.t_amb[1]
		elif s == 't_suelo' and zona == 2:
			yield self.t_suelo[1]
		elif s == 't_agua' and zona == 2:
			yield self.t_agua[1]
		elif s == 't_amb' and zona == 3:
			yield self.t_amb[2]
		semTelemetry.release()


			

	def cambiar_consigna(self, num, zona, flag_user):
		sem2.acquire()
		semConsignas.acquire()
		global flag_cambiado
		if flag_user==1:
			flag_cambiado[zona+1][0]=1
			flag_cambiado[zona+1][1]=calendar.timegm(time.gmtime())
		if num < 10 and num!=1 and (num==-1 and self.consignas[zona]+num<10):
			self.consignas[zona] = self.consignas[zona]
		elif num == 1 or (num==-1 and self.consignas[zona]+num>=10):
			self.consignas[zona] = self.consignas[zona] + num
		else:
			self.consignas[zona] = num

		if zona == 0:
			self.root.ids.cons_z1_inv_conf.text = str(self.consignas[zona])
			self.root.ids.cons_z1_ver_conf.text = str(self.consignas[zona])
		elif zona == 1:
			self.root.ids.cons_z2_inv_conf.text = str(self.consignas[zona])
			self.root.ids.cons_z2_ver_conf.text = str(self.consignas[zona])

		with open("/home/pi/ASIGEO/json_f/pantalla" + str(zona + 1) + ".json", 'r+') as f:
			pant = json.load(f)
			pant['consigna'] = self.consignas[zona]
			f.seek(0)
			json.dump(pant, f,indent=4)
		semConsignas.release()
		sem2.release()

	def cambiar_cons_reducido(self, num, zona, modo):
		zona = zona - 1
		semConsignas.acquire()
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
		semConsignas.release()

	def cambiar_cons_apagado(self, num, zona, modo):
		zona = zona - 1
		semConsignas.acquire()
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
		semConsignas.release()
	def build(self):
		logging.info("Primero1")
		self.root = Builder.load_file('kv/main.kv')

	@mainthread
	def actualizar_labels(self):
		if not self.ch_errors[0]:
			self.root.ids.t_ext0.text ='[b]T EXTERIOR: ' + '[color=006CFF]' + str(self.t_ext) + ' [/color][/b]'
			self.root.ids.t_ext1.text = str(self.t_ext)
			self.root.ids.t_ext2.text = str(self.t_ext)
			self.root.ids.t_ext3.text = str(self.t_ext)
			self.root.ids.t_exterior.text = str(self.t_ext)
		else:
			self.root.ids.t_ext0.text = '[b]T EXTERIOR: ' + '[color=BE1515]' + 'ERROR' + ' [/color][/b]'
			self.root.ids.t_ext1.text = '[color=F14108] Error [/color]'
			self.root.ids.t_ext2.text = '[color=F14108] Error [/color]'
			self.root.ids.t_ext3.text = '[color=F14108] Error [/color]'
			self.root.ids.t_exterior.text = '[color=F14108] Error [/color]'

		if not self.ch_errors[1]:

			self.root.ids.t_suelo_z1.text = str(self.t_suelo[0])
		else:

			self.root.ids.t_suelo_z1.text = '[color=F14108] Error [/color]'

		if not self.ch_errors[2]:

			self.root.ids.t_agua_z1.text = str(self.t_agua[0])
			self.root.ids.t_agua_z1_p0.text = '[b]'+str(self.t_agua[0]) + 'ºC [/b]'
		else:

			self.root.ids.t_agua_z1.text = '[color=F14108] Error [/color]'
			self.root.ids.t_agua_z1_p0.text = '[color=F14108] Error [/color]'

		if not self.ch_errors[3]:
			self.root.ids.t_amb1.text = str(self.t_amb[0])
			self.root.ids.t_amb_z1.text = str(self.t_amb[0])
			self.root.ids.t_amb_z1_p0.text = '[b]' + str(self.t_amb[0]) + 'ºC[/b]'
		else:
			self.root.ids.t_amb1.text = '[color=F14108] Error [/color]'
			self.root.ids.t_amb_z1.text = '[color=F14108] Error [/color]'
			self.root.ids.t_amb_z1_p0.text = '[color=F14108] Error [/color]'

		if not self.ch_errors[4]:

			self.root.ids.t_suelo_z2.text = str(self.t_suelo[1])
		else:

			self.root.ids.t_suelo_z2.text = '[color=F14108] Error [/color]'

		if not self.ch_errors[5]:

			self.root.ids.t_agua_z2.text = str(self.t_agua[1])
			self.root.ids.t_agua_z2_p0.text ='[b]' + str(self.t_agua[1]) + 'ºC [/b]'
		else:

			self.root.ids.t_agua_z2.text = '[color=F14108] Error [/color]'
			self.root.ids.t_agua_z2_p0.text = '[color=F14108] Error [/color]'

		if not self.ch_errors[6]:
			self.root.ids.t_amb2.text = str(self.t_amb[1])
			self.root.ids.t_amb_z2.text = str(self.t_amb[1])
			self.root.ids.t_amb_z2_p0.text = '[b]' + str(self.t_amb[1])+'ºC [/b]'
		else:
			self.root.ids.t_amb2.text = '[color=F14108] Error [/color]'
			self.root.ids.t_amb_z2.text = '[color=F14108] Error [/color]'
			self.root.ids.t_amb_z2_p0.text = '[color=F14108] Error [/color]'

		if not self.ch_errors[7]:
			self.root.ids.t_amb3.text = str(self.t_amb[2])
			self.root.ids.t_amb_z3.text = str(self.t_amb[2])
			self.root.ids.t_amb_z3_p0.text = '[b]' + str(self.t_amb[2]) +'ºC [/b]'

		else:
			self.root.ids.t_amb3.text = '[color=F14108] Error [/color]'
			self.root.ids.t_amb_z3.text = '[color=F14108] Error [/color]'
			self.root.ids.t_amb_z3_p0.text = '[color=F14108] Error [/color]'

	@mainthread
	def etiquetas_mod(self, sched, zona):
		logging.info(self.consignas[zona])
		if zona == 0:
			try:
				self.root.ids.t_des_z1_p0.text = str(self.consignas[zona])
			except:
				logging.info("Error kivy zona 1 consignas p0")
			try:
				if sched == 0:
					self.root.ids.modo_z1.text = 'CONFORT'

				elif sched == 1:
					self.root.ids.modo_z1.text = 'REDUCIDO'
				else:
					self.root.ids.modo_z1.text = 'APAGADO'
			except:
				logging.info("Error kivy zona 1 modo p0")

		elif zona == 1:
			try:
				self.root.ids.t_des_z2_p0.text = str(self.consignas[zona])
				self.root.ids.t_des_z3_p0.text = str(self.consignas[2])
			except:
				logging.info("Error kivy zona 2 consignas p0")

			try:
				if sched == 0:
					self.root.ids.modo_z2.text = 'CONFORT'
				elif sched == 1:
					self.root.ids.modo_z2.text = 'REDUCIDO'
				else:
					self.root.ids.modo_z2.text = 'APAGADO'
			except:
				logging.info("Error kivy confort p0")
	@mainthread
	def cambioZonaUI(self, zona, func):
		if zona == 0:
			if func == 1 or func == 2:
				self.root.ids.abriendo1.text = 'Abriendo'
				self.root.ids.est_reg_z1_p0.text = 'Abriendo'
			elif func == 3:
				self.root.ids.abriendo1.text = 'Cerrando'
				self.root.ids.est_reg_z1_p0.text = 'Cerrando'
			else:
				self.root.ids.abriendo1.text = 'T Correcta'
				self.root.ids.est_reg_z1_p0.text = 'T Correcta'
		elif zona == 1:
			if func == 1 or func == 2:
				self.root.ids.abriendo2.text = 'Abriendo'
				self.root.ids.est_reg_z2_p0.text = 'Abriendo'
			elif func == 3:
				self.root.ids.abriendo2.text = 'Cerrando'
				self.root.ids.est_reg_z2_p0.text = 'Cerrando'
			else:
				self.root.ids.abriendo2.text = 'T Correcta'
				self.root.ids.est_reg_z2_p0.text = 'T Correcta'
	@mainthread
	def cambiodirectaUI(self, funcionando):
		try:
			if funcionando:
				self.root.ids.abriendo3.text = 'Encendido'
			else:
				self.root.ids.abriendo3.text = 'Apagado'

		except:
			logging.info("KV no inicializado")

	@mainthread
	def horaUI(self, ahora):
		hour = "{:0>2d}".format(ahora.hour)
		min = "{:0>2d}".format(ahora.minute)
		day = "{:0>2d}".format(ahora.day)
		mth = "{:0>2d}".format(ahora.month)
		year = str(ahora.year)
		try:
			self.root.ids.hora.text = hour +':' + min
			self.root.ids.fecha.text = day + '/' + mth + '/' + year
		except:
			logging.info(Exception)

def lectura_sondas(app):
	time.sleep(60)
	contador = 10
	arr_tamb1 = np.zeros(5)
	arr_tamb2 = np.zeros(5)
	arr_text = np.zeros(5)
	arr_tsuelo1 = np.zeros(5)
	arr_tsuelo2 = np.zeros(5)

	while True:
		app.readSensors()
		arr_tamb1 = np.roll(arr_tamb1, 1)
		arr_tamb2 = np.roll(arr_tamb2, 1)
		arr_text = np.roll(arr_text, 1)
		arr_tsuelo1 = np.roll(arr_tsuelo1, 1)
		arr_tsuelo2 = np.roll(arr_tsuelo2, 1)

		arr_text[0] = app.chanels[0]
		arr_tsuelo1[0] = app.chanels[1]
		arr_tsuelo2[0] = app.chanels[4]

		arr_tamb1[0] = app.chanels[3]
		arr_tamb2[0] = app.chanels[6]

		if contador == 10:
			semTelemetry.acquire()
			app.t_agua[0] = round(app.chanels[2], 1)
			app.t_agua[1] = round(app.chanels[5], 1)  # Esto hay que cambiarlo luego, SOLO TEST
			app.t_ext = round(np.mean(arr_text), 1)
			app.t_suelo[0] = round(np.mean(arr_tsuelo1), 1)
			app.t_amb[0] = round(np.mean(arr_tamb1), 1)
			app.t_suelo[1] = round(np.mean(arr_tsuelo2), 1)  # SOLO TEST
			app.t_amb[1] = round(np.mean(arr_tamb2), 1)
			app.t_amb[2] = round(app.chanels[7], 1)
			sem1.acquire()
			sensor_data = createJSON([[app.t_suelo[0],app.t_amb[0],app.t_agua[0]],[app.t_suelo[1],app.t_amb[1],app.t_agua[1]],[app.t_amb[2]],[app.t_ext]])
			global telemetry
			telemetry = [sensor_data.encode("utf-8")] + telemetry
			sem1.release()
			try:
				app.actualizar_labels()
				"""if comprobarConexion():
					self.root.ids.conexion.source = "data/internet.png"
				else:
					self.root.ids.conexion.source = "data/nointernet.png"""
				contador = 0

			except:
				logging.info("Error de carga")
			semTelemetry.release()
		time.sleep(3)
		contador += 1


def main_directa(app, zona):
	time.sleep(30)
	zona = zona - 1
	while True:
		app.zona_directa.t_amb = app.t_amb[zona]
		app.zona_directa.consigna = app.consignas[zona]
		funcionando = app.zona_directa.logica(app.modo)
		time.sleep(5)
		logging.info("Valor de funcionando: " + str(funcionando))
		app.cambiodirectaUI(funcionando)


def main(app, zona):
	time.sleep(60)
	zona = zona - 1
	while True:
		try:
			while True:
				ahora = datetime.now()
				hora = ahora.hour
				if(zona==1):
					app.horaUI(ahora)


				dia = datetime.weekday(ahora)
				semScheduler.acquire()
				sched = app.scheduler[zona,dia, hora]
				semScheduler.release()

				if app.act_seguridades == 1:
					app.logicas[zona].act_seguridades()
					app.act_seguridades = 0
				app.logicas[zona].sonda_exterior = app.t_ext
				app.logicas[zona].sonda_ambiente = app.t_amb[zona]
				app.logicas[zona].sonda_agua = app.t_agua[zona]
				app.logicas[zona].sonda_suelo = app.t_suelo[zona]
				app.logicas[zona].modo_bomba = app.bombas[zona]
				app.logicas[zona].modo_curva = app.curvas[zona]
				if sched == 0:
					if app.modo == 'invierno':
						app.logicas[zona].consigna = app.consignas[zona]
					elif app.modo == 'verano':
						app.logicas[zona].consigna = app.consignas[zona]
				elif sched == 1:
					if app.modo == 'invierno':
						app.logicas[zona].consigna = app.reducido_inv[zona]
					elif app.modo == 'verano':
						app.logicas[zona].consigna = app.reducido_ver[zona]
				elif sched == 2:
					if app.modo == 'invierno':
						app.logicas[zona].consigna = app.apagado_inv[zona]
					elif app.modo == 'verano':
						app.logicas[zona].consigna = app.apagado_ver[zona]

				app.etiquetas_mod(sched, zona)
				if False: #self.error:#Esto cuando sepamos que va bien descomentar
					app.logicas[zona].seguridad()
					time.sleep(5)
				else:
					func = app.logicas[zona].logica(app.modo)
					logging.info("zona " + str(zona) + "funcionando" + str(func))


				app.cambioZonaUI(zona, func)
				time.sleep(1)

		finally:
			logging.info("Error")





if __name__ == '__main__':
	MainApp().run()