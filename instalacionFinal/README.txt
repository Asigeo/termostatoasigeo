Aquí se indican las instrucciones a seguir durante la instalación:

 - Pre-requisitos:
 	1. El dispositivo al que se le realice la instalación tiene que
 		poder establecerse una conexión ssh.
 	2. En la instalación se deben de contar con dos ficheros:
 		- ASIGEO.zip
 		- instalacionASIGEO.sh
 	3. Ambos archivos deben de encontrase en el dispositivo, en caso contrario
 		se debe realizar un scp a la máquina con dicho archivos.

 	4. Se realizará ssh al dispositivo en cuestion.
 	5. Siempre asegurar que se tienen los privilegios necesarios.
 	6. Los equipos tienen que tener un usuario pi con privilegios sudo.

 - Advertencias:
 	- El ejecutable "server" solo funciona para distribución debian6 (misma versión que tiene instalada el equipo de test facilitado por ASIGEO).
 	- Después, si el usuario quiere, puede borrar los ficheros enviados por scp.
 	- La contraseña que se introduzca por el usuario debe de ser previamente notificada por nosotros. (necesaria para la conexión con la plataforma)


 - Pasos:

 	- La instalación crea una carpeta ASIGEO en el directorio /home/pi
 	- La instalación chequea si esta ya una versión previa o una instalación si es así la sobre-escribe.
 	- La instalación descomprime la nueva versión y posteriormente solicita que se especifique una password.
 	- Una vez introducida la password la instalación la almacenará en un fichero token.ini.
 		- Si este fichero se edita se editará la password al dispositivo en la nube.
 	- Tras este paso establecerá que la app comience en el arranque.
 	- Finalmente pedirá si se quiere reiniciar el equipo.
 		(CUIDADO: Los cambios solo se realizaran si se reinicia el equipo sino
 		la app no correrá automáticamente)
 