#!/bin/bash

PATH_DIR="/home/pi/ASIGEO/"
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
		echo $PASS
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
if [ ! -f "/etc/rc.local" ]
then 
	echo "Fichero rc.local no existe en el equipo"
	exit 1
else
	echo "#!/bin/sh" > /etc/rc.local
	echo "_IP=\$(hostname -I) || true" >> /etc/rc.local
	echo "if [ \"$_IP\" ]; then" >> /etc/rc.local
	echo "	printf \"My IP address is %s\n\" \"$_IP\"" >> /etc/rc.local
	echo "fi" >> /etc/rc.local

	echo "sudo /home/pi/ASIGEO/server &" >> /etc/rc.local
	echo "sudo python3 /home/pi/ASIGEO/Main1Pant.py &" >> /etc/rc.local
	echo "sudo python3 /home/pi/ASIGEO/ScreenTimer.py &" >> /etc/rc.local

	echo "exit 0" >> /etc/rc.local
fi

echo "Instalando dependencias necesarias"
sudo pip3 install -r requirements.txt

echo "Instalacion terminada"
sleep 1
echo "[Escribe: [Y|y] para confirmar u otra caso para denegar]"
read -p "Quiere reiniciar ahora?\n"$OPTION  -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
    sudo reboot
fi