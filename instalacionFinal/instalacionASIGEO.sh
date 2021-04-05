#!/bin/bash

PATH_DIR="/home/pi/ASIGEO/"
PATH_KIVY="/root/"
ZIP="ASIGEO.zip"

echo "Realizando instalación de equipo ASIGEO"
echo "==========================================================="
echo "==========================================================="
sleep 1

echo "El directorio de despliegue será: " $PATH_DIR
sleep 1

if [ ! -d $PATH_DIR ]
then 
	sudo mkdir $PATH_DIR
else
	echo "Removiendo antigua versión de App"
	sleep 1
	PATHCOMPLETE=$PATH_DIR
	sudo rm -r $PATHCOMPLETE
	echo "Versión antigua eliminada"
	sleep 1
	sudo mkdir $PATH_DIR
fi

if [ ! -f "ASIGEO.zip" ]
then
	echo "No se encontro el fichero zip para la instalación"
	sleep 1
	exit 1
fi

echo "Ahora se procede a la instalación de nueva verisión"

echo "Copiando zip con nueva versión de ASIGEO a directorio de despliegue"
sleep 1
sudo cp $ZIP $PATH_DIR
echo "Copiado zip con nueva versión"
sleep 1

echo "Extrayendo nueva versión de App"
sleep 1
sudo unzip -d $PATH_DIR $ZIP
echo "App ASIGEO extraida"
sleep 1

echo "Peticion de token para device"
sleep 1
PATHCOMPLETE=$PATH_DIR"token.ini"
echo "[Escriba: La contraseña que desee para su dispositivo]"
echo "Press enter cuando termine de escribirla"
PASS=""
while : ; do
	read -n 1 k <&1
	if [[ $k = "" ]] ; then
		printf "\nQuitting from the program\n"
		break
	else
		PASS="$PASS$k"
	fi
done
echo "La contraseña será: " $PASS
if [[ $PASS ]]
then
	sudo echo "[SECURITY]" > $PATHCOMPLETE
    echo "token="$PASS >> $PATHCOMPLETE
fi

echo "Estableciendo App para que se ejecute en boot"
sleep 1
echo "Estableciendo servicio server Inar"
sleep 1
if [ ! -f "/etc/systemd/system/serverInar.service" ]
then 
	sudo cp serverInar.service /etc/systemd/system/
else
	echo "[Escribe: [Y|y] para confirmar u otra caso para denegar]"
	read -p "Quiere reescribir el fichero del servicio?\n"$OPTION  -n 1 -r
	if [[ $REPLY =~ ^[Yy]$ ]]
	then
	    sudo cp serverInar.service /etc/systemd/system/
	fi
fi
echo "Estableciendo servicio Asigeo App"
sleep 1
if [ ! -f "/etc/systemd/system/asigeoApp.service" ]
then 
	sudo cp asigeoApp.service /etc/systemd/system/
else
	echo "[Escribe: [Y|y] para confirmar u otra caso para denegar]"
	read -p "Quiere reescribir el fichero del servicio?\n"$OPTION  -n 1 -r
	if [[ $REPLY =~ ^[Yy]$ ]]
	then
	    sudo cp asigeoApp.service /etc/systemd/system/
	fi
fi
echo "Estableciendo servicio screen timer"
sleep 1
if [ ! -f "/etc/systemd/system/screenService.service" ]
then 
	sudo cp screenService.service /etc/systemd/system/
else
	echo "[Escribe: [Y|y] para confirmar u otra caso para denegar]"
	read -p "Quiere reescribir el fichero del servicio?\n"$OPTION  -n 1 -r
	if [[ $REPLY =~ ^[Yy]$ ]]
	then
	    sudo cp screenService.service /etc/systemd/system/
	fi
fi

sudo systemctl daemon-reload
sudo systemctl enable serverInar.service
sudo systemctl enable asigeoApp.service
sudo systemctl enable screenService.service

echo "Instalando dependencias necesarias"
sudo apt-get -y update
sudo apt-get -y full-upgrade
sudo apt-get install -y python3-pip
sudo pip3 install -r requirements.txt
sudo apt-get install -y libatlas-base-dev
sudo apt-get install -y \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libportmidi-dev \
    libswscale-dev \
    libavformat-dev \
    libavcodec-dev \
    zlib1g-dev
sudo apt-get install -y \
    libgstreamer1.0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good
sudo apt-get install -y libmtdev-dev
sudo apt-get install -y xclip

echo "Escribiendo el fichero de configuracion de kivy"
sleep 1 
if [ ! -d "/root/.kivy" ]
then 
	sudo mkdir /root/.kivy
	sudo cp config.ini /root/.kivy/
else
	echo "[Escribe: [Y|y] para confirmar u otra caso para denegar]"
	read -p "Quiere reescribir el fichero de configuracion de kivy?\n"$OPTION  -n 1 -r
	if [[ $REPLY =~ ^[Yy]$ ]]
	then
	    sudo cp config.ini /root/.kivy/
	fi
fi
echo "Instalacion terminada"
sleep 1
echo "[Escribe: [Y|y] para confirmar u otra caso para denegar]"
read -p "Quiere reiniciar ahora?\n"$OPTION  -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
    sudo reboot
fi