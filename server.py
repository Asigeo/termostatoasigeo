'''(c) 2018 InarTecnologias and its subsidiaries. 
    
    Subject to your compliance with these terms, you may use InarTecnologias software and any 
    derivatives exclusively with InarTecnologias products. It is your responsibility to comply with third party 
    license terms applicable to your use of third party software (including open source software) that 
    may accompany InarTecnologias software.
    
    THIS SOFTWARE IS SUPPLIED BY INARTECNOLOGIAS "AS IS". NO WARRANTIES, WHETHER 
    EXPRESS, IMPLIED OR STATUTORY, APPLY TO THIS SOFTWARE, INCLUDING ANY 
    IMPLIED WARRANTIES OF NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS 
    FOR A PARTICULAR PURPOSE.
    
    IN NO EVENT WILL INARTECNOLOGIAS BE LIABLE FOR ANY INDIRECT, SPECIAL, PUNITIVE, 
    INCIDENTAL OR CONSEQUENTIAL LOSS, DAMAGE, COST OR EXPENSE OF ANY KIND 
    WHATSOEVER RELATED TO THE SOFTWARE, HOWEVER CAUSED, EVEN IF INARTECNOLOGIAS 
    HAS BEEN ADVISED OF THE POSSIBILITY OR THE DAMAGES ARE FORESEEABLE. TO 
    THE FULLEST EXTENT ALLOWED BY LAW, INARTECNOLOGIAS'S TOTAL LIABILITY ON ALL 
    CLAIMS IN ANY WAY RELATED TO THIS SOFTWARE WILL NOT EXCEED THE AMOUNT 
    OF FEES, IF ANY, THAT YOU HAVE PAID DIRECTLY TO INARTECNOLOGIAS FOR THIS 
    SOFTWARE.'''

import paho.mqtt.client as paho  # mqtt library
import json
import logging
from tb_rest_client.rest_client_ce import *
from tb_rest_client.rest import ApiException
from tb_rest_client.api.api_ce import *
import time
import random
import threading
import socket
import sys
import time
import threading
import selectors
import types
import configparser

sem = threading.Semaphore()

events = selectors.EVENT_READ | selectors.EVENT_WRITE


sensor_data = {'temperature': 100.0, 'humedad': 210.0}
json_dump = json.dumps(sensor_data)

telemetry = [json_dump.encode("utf-8")]

envioMSG=""
ultenvioMSG=[]


def on_message(client, userdata, message):  # The callback\n for when a PUBLISH message is received from the server.
	print("Message received", message.payload)  # Print a received msg
	sem.acquire()
	global envioMSG
	print(envioMSG)
	envioMSG = message.payload.decode("utf-8")
	sem.release()

def on_subscribe(client, userdata, mid, granted_qos):
	print("Se ha suscrito uno")

def on_connect(client, userdata, flags, rc):
	print("Se ha conectado uno: ", client)
	print("Connected with result code "+str(rc))
	client.subscribe("v1/devices/me/attributes", 1)

def on_disconnect(client, userdata, rc):
	print("Se ha desconectado uno: ", client)
	print("Connected with result code "+str(rc))

class Server:
	port=0
	hostname=0
	daemon=True
	sock=0
	clientnames=0
	n_clients=0
	asincrono_ = 1
	sel = 0

	def __init__(self, p=43134, h='localhost'):
		self.hostname = h
		self.port = p
		print("Voy a definir un socket")
		print(socket.socket(socket.AF_INET,socket.SOCK_STREAM))
		self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		print("Definido un socket")
		self.sel = selectors.DefaultSelector()
		self.clientnames=[]

	def asincrono(self):
		self.sock.setblocking(False)
		self.asincrono_ = 0

	def sincrono(self):
		self.sock.setblocking(True)
		self.asincrono_ = 1

	def isAsincrono(self):
		return self.asincrono_ == 0

	def addSelector(self, data):
		self.sel.register(self.sock, selectors.EVENT_READ, data)

	def startServer(self):
		print("Intento realizar bind")
		self.sock.bind((self.hostname,self.port))
		print("Escuchando conexiones")
		self.sock.listen(1)
		print("Servidor inicializado")

	def acceptClient(self):
		(clientname,address)=self.sock.accept()

		if self.asincrono_==0:
			clientname.setblocking(False)
			data = types.SimpleNamespace(addr=address, connid=0,
                                     recv_total=0,
                                     outb=[])
			self.sel.register(clientname, events, data)

		self.clientnames = [clientname] + self.clientnames
		self.n_clients = self.n_clients + 1
		return clientname, address, self.n_clients - 1

	def receiveClient(self, i):
		return self.clientnames[i].recv(1024)

	def sendClient(self,i,msg):
		return self.clientnames[i].send(msg)

	def sendAllClients(self, msg):
		for client in self.clientnames:
			client.send(msg)

	def setClients(self, list_clients):
		for client in list_clients:
			self.clientnames = [client] + self.clientnames
			self.n_clients = self.n_clients + 1

	def setHostname(self, host):
		self.hostname = host

	def setPort(self, port):
		self.port = port

	def getHostname(self):
		return self.hostname

	def getPort(self):
		return self.port

	def getClients(self):
		return self.clientnames

	def getNumberClients(self):
		return self.n_clients

	def disconnect(self):
		self.sock.close()

	def disconnectClient(self,i):
		self.clientnames[i].close()

	def getSelector(self):
		return self.sel.select(timeout=None)

	def getSel(self):
		return self.sel

	def unregisterSock(self, sock):
		print("Listado de clientes " , self.hostname, ": ", self.clientnames)
		self.sel.unregister(self.clientnames[0])


class ServerAPI():
	servers=[]
	n_servers=0
	socks=[]
	serve_side = 0

	def __init__(self, p=51234, h='localhost'):
		self.server_side = Server(p, h)

	def getServer(self, hostname):
		i = 0
		for server in self.servers:
			if server == hostname:
				return i
			i = i + 1
		
		return -1

	def getServerSide(self):
		return self.server_side

	def setServerSide(self, server_):
		self.server_side = server_

	def connect(self,host,port, data=None):
		sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		if self.server_side.isAsincrono():
			sock.setblocking(False)
		self.socks = [sock] + self.socks
		self.socks[0].connect_ex((host,port))
		self.n_servers = self.n_servers + 1
		self.servers=[host] + self.servers
		if self.server_side.isAsincrono():
			self.server_side.getSel().register(self.socks[0], events, data)

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

	def disconnectFromServer(self):
		for client in self.socks:
			client.close()


class ServerAPITB():
	client = paho.Client('TBTest', clean_session=True, userdata=None, protocol=paho.MQTTv311, transport="tcp")
	tb_host = "thingsboard.cloud"
	tb_port = 1883

	ACCESS_TOKEN_TB = ''

	servers=[]
	n_servers=0
	socks=[]
	server_side=0

	def __init__(self, port=51232, hostname='localhost', tb="thingsboard.cloud", tb_p=1883):
		self.server_side = Server(port, hostname)
		print("Soy: ", self.client)
		self.tb_host = tb
		self.tb_port = tb_p

	def connectTB(self):
		print("Parametros conexión: ", self.tb_host, self.tb_port)
		self.client.loop_start()
		self.client.connect(self.tb_host, port=self.tb_port, keepalive=60, bind_address="")
		#self.client.reconnect_delay_set(min_delay=1, max_delay=120)

	def getServerSide(self):
		return self.server_side

	def setServerSide(self, server_):
		self.server_side = server_

	def setCredentials(self, ACCESS_TOKEN):
		self.client.username_pw_set(ACCESS_TOKEN)
		self.ACCESS_TOKEN_TB = ACCESS_TOKEN

	def getCredentials(self):
		return self.ACCESS_TOKEN_TB

	def getTBHost(self):
		return self.tb_host

	def setTBHost(self, host):
		self.tb_host = host

	def disconnectTB(self):
		self.client.disconnect()

	def sendTB(self, dest, data):
		self.client.publish(dest, data, 1)

	def getServer(self, hostname):
		i = 0
		for server in self.servers:
			if server == hostname:
				return i
			i = i + 1
		
		return -1

	def connect(self,host,port, data=None):
		sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		if self.server_side.isAsincrono():
			sock.setblocking(False)
		self.socks = [sock] + self.socks
		self.socks[0].connect_ex((host,port))
		self.n_servers = self.n_servers + 1
		self.servers=[host] + self.servers
		if self.server_side.isAsincrono():
			self.server_side.getSel().register(self.socks[0], events, data)

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

	def disconnectFromServer(self):
		for client in self.socks:
			client.close()


	def setMQTTClientOnMessage(self):
		self.client.on_message = on_message
		self.client.on_subscribe = on_subscribe
		self.client.on_connect = on_connect
		self.client.on_disconnect = on_disconnect
		self.client.message_callback_add("v1/devices/me/attributes", on_message)

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


def equalMsg(envioMSG, ultenvioMSG):
	a = json.loads(envioMSG)
	b = json.loads(ultenvioMSG[0])
	print("Comparativa entre mensjes: ", a,b)
	return sorted(a.items()) == sorted(b.items())

def service_connectionAPI(key, mask, client, host):
	sock = key.fileobj
	data = key.data
	global ultenvioMSG
	if mask & selectors.EVENT_READ:
		if(client.getServerSide().getHostname()!='127.0.0.2'):
			try:
				recv_data = client.receiveMsg(host)  # Should be ready to read
			except Exception as error:
				recv_data = b''
			####segun recibdo el server lo que hago es crear hilo con la petición
			if recv_data:
				print(client.getServerSide().getHostname(),' recibido del server ', repr(recv_data))
				recv_data = recv_data.decode("utf-8").split("\n")
				print(client.getServerSide().getHostname(),' recibido del server ', repr(recv_data))
				if(len(recv_data)>1):
					recv_data = recv_data[0:len(recv_data)-1]
				print(client.getServerSide().getHostname(),' recibido del server ', repr(recv_data))
				while recv_data:
					data.outb = data.outb + ['S' + recv_data[0]]
					recv_data = recv_data[1:]
			else:
				pass
		try:
			recv_data = client.getServerSide().receiveClient(0)
		except Exception as error:
			recv_data = b''
		if recv_data:
			print(client.getServerSide().getHostname(),' recibido del cliente ', repr(recv_data))
			recv_data = recv_data.decode("utf-8").split("\n")
			print(client.getServerSide().getHostname(),' recibido del cliente ', repr(recv_data))
			if(len(recv_data)>1):
				recv_data = recv_data[0:len(recv_data)-1]
			print(client.getServerSide().getHostname(),' recibido del cliente ', repr(recv_data))
			while recv_data:
				data.outb = data.outb + ['C' + recv_data[0]]
				recv_data = recv_data[1:]

	elif (client.getServerSide().getHostname()=='127.0.0.2'):
		sem.acquire()
		global envioMSG
		if envioMSG != "" and not equalMsg(envioMSG, ultenvioMSG):
			ultenvioMSG.pop()
			print(client.getServerSide().getHostname(),' recibido del server TB ', repr(envioMSG))
			envioMSG=envioMSG+'\n'
			sent = client.getServerSide().sendClient(0, envioMSG.encode("utf-8"))  # Should be ready to write
			envioMSG = envioMSG[sent+1:]
		else:
			envioMSG = ""
		sem.release()

	if mask & selectors.EVENT_WRITE:
		if data.outb:
			s = data.outb[0]
			print("Mensaje Original: ", s) 
			if s[0] == 'C':
				if (client.getServerSide().getHostname()!='127.0.0.2'):
					s=s[1:]
					s=s+'\n'
					print(client.getServerSide().getHostname(),' sending ',repr(s))
					sent = client.sendMsg(s.encode("utf-8"), host)  # Should be ready to write
					data.outb[0] = data.outb[0][sent+1:]
					if len(data.outb[0])==0:
						data.outb = data.outb[1:]
				###rutina de TB
				if(client.getServerSide().getHostname()=='127.0.0.2' and s!='Cack'):
					s=s[1:]
					print("Telemetría enviada: ", json.loads(s))
					if 'modo' in s:
						client.sendTB('v1/devices/me/attributes', s)
						ultenvioMSG.append(s)
					elif 'consignaZona1' in s:
						client.sendTB('v1/devices/me/attributes', s)
						ultenvioMSG.append(s)
					elif 'consignaZona2' in s:
						client.sendTB('v1/devices/me/attributes', s)
						ultenvioMSG.append(s)
					elif 'consignaZona3' in s:
						client.sendTB('v1/devices/me/attributes', s)
						ultenvioMSG.append(s)
					else:
						client.sendTB('v1/devices/me/telemetry', s)
						ultenvioMSG.append(s)
					data.outb = data.outb[1:]
					data.outb = ['Sack'] + data.outb
				elif(client.getServerSide().getHostname()=='127.0.0.2' and s=='Cack'):
					data.outb = data.outb[1:]
			elif s[0] == 'S':
				s=s[1:]
				s=s+'\n'
				print(client.getServerSide().getHostname(),' sending ',repr(s))
				sent = client.getServerSide().sendClient(0, s.encode("utf-8"))  # Should be ready to write
				data.outb[0] = data.outb[0][sent+1:]
				if len(data.outb[0])==0:
					data.outb = data.outb[1:]

def accept_wrapper1(server):
	conn, addr, i = server.getServerSide().acceptClient()  # Should be ready to read
	print('Server API accepted connection from ', addr)


def DemoServerAPI(port, host, portServer, hostServer):
		print("Soy el otro servidor")
		server = ServerAPI(port, host)
		server.getServerSide().asincrono()
		print("Me establezco como server")
		server.getServerSide().startServer()
		#print("Selectors del API: ", server.getServerSide().getSelector())
		data = types.SimpleNamespace(addr=(hostServer,portServer), inb=[], outb=[])
		print('Server API starting connection', 0, 'to', (hostServer,portServer))
		server.connect(hostServer, portServer, data=data)
		print("Me he conectado")
		server.getServerSide().addSelector(None)
		while True:
			events = server.getServerSide().getSelector()
			for key, mask in events:
				if key.data is None:
					accept_wrapper1(server)
				else:
					service_connectionAPI(key, mask, server,hostServer)

def DemoServerAPITB(port, host, portServer, hostServer):
		print("Comienzo el programa")
		server = ServerAPITB(port, host)
		print("Voy a establecer el socket asincrono")
		server.getServerSide().asincrono()
		print("Me establezco como server")
		server.getServerSide().startServer()
		#print("Selectors del API: ", server.getServerSide().getSelector())
		server.getServerSide().addSelector(None)
		server.setMQTTClientOnMessage()  # Define callback\n function for receipt of a message
		config = configparser.ConfigParser()
		config.read('/home/pi/ASIGEO/token.ini')
		server.setCredentials(config['SECURITY']['token'])# Connect to ThingsBoard using default MQTT port and 60 seconds keepalive interval
		server.connectTB()
		while True:
			events = server.getServerSide().getSelector()
			for key, mask in events:
				if key.data is None:
					accept_wrapper1(server)
				else:
					service_connectionAPI(key, mask, server,hostServer)


if __name__ == "__main__":
	t1 = threading.Thread(target=DemoServerAPITB, args=(51412,'127.0.0.2',51412,'127.0.0.1',))
	t1.start()
	x = threading.Thread(target=DemoServerAPI, args=(51412,'127.0.0.3',51412,'127.0.0.2',))
	x.start()
