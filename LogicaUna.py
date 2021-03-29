import json
from time import sleep
from Relay_Module import Relees


# funcionando = 0 parar
# funcionando = 1 abriendo largo
# funcionando = 2 abriendo corto
# funcionando = 3 cerrando largo
reles = Relees()

def curva(x, b, m):
    y = b - m * x
    return y
class LogicaZonaDirecta:
    def __init__(self,rele):
        self.t_amb = 20
        self.consigna = 20
        self.modo = 'invierno'
        self.rele = rele

    def logica(self,modo):
        funcionando = 0
        if modo == 'invierno':
            if self.consigna > self.t_amb:
                funcionando = 1
                reles.relayon(self.rele)
            else:
                reles.relayoff(self.rele)
                funcionando = 0
        elif modo == 'verano':

            if self.consigna < self.t_amb:
                reles.relayon(self.rele)
                funcionando = 1
            else:
                reles.relayoff(self.rele)
                funcionando = 0
        else:
            reles.relayoff(self.rele)
            funcionando = 0

        return funcionando

                
            


class LogicaZona:
    TEMP_LARGA = 6
    TEMP_CORTA = 2

    def __init__(self, zona):
        # seguridades
        self.zona = zona
        self.sched = False
        self.temporizador = 0
        self.modo_bomba = False  # False = Continua  True = Termostato
        self.grado_confort = 0
        self.modo_curva = 0  # 0 modo normal #1 modo intenso # 2 reducido

        self.sonda_exterior = 0
        self.sonda_ambiente = 0
        self.sonda_agua = 0
        self.sonda_suelo = 0
        self.funcionando = 0
        self.invierno = True
        self.verano = False
        self.antihielo = False
        
        self.consigna = 20
        with open('/home/pi/ASIGEO/json_f/seguridades.json', 'r') as file:
            seguridades = json.load(file)
        # seguridades
        if zona == 1:
            self.inv_tmax_agua = seguridades["inv_tmax_agua1"]
            self.inv_tmax_suelo = seguridades["inv_tmax_suelo1"]
            self.inv_tmin_suelo = seguridades["inv_tmin_suelo1"]
            self.ver_tmin_agua = seguridades["ver_tmin_agua1"]
            self.ver_tmin_suelo = seguridades["ver_tmin_suelo1"]
            self.ant_tmax_agua = seguridades["ant_tmax_agua1"]
            self.ant_tmin_agua = seguridades["ant_tmin_agua1"]
            self.ant_tmin_suelo = seguridades["ant_tmin_suelo1"]
        elif zona == 2:
            self.inv_tmax_agua = seguridades["inv_tmax_agua2"]
            self.inv_tmax_suelo = seguridades["inv_tmax_suelo2"]
            self.inv_tmin_suelo = seguridades["inv_tmin_suelo2"]
            self.ver_tmin_agua = seguridades["ver_tmin_agua2"]
            self.ver_tmin_suelo = seguridades["ver_tmin_suelo2"]
            self.ant_tmax_agua = seguridades["ant_tmax_agua2"]
            self.ant_tmin_agua = seguridades["ant_tmin_agua2"]
            self.ant_tmin_suelo = seguridades["ant_tmin_suelo2"]

        self.ant_tmin_ext = seguridades["ant_tmin_ext"]
        self.ver_tmin_ext = seguridades["ver_tmin_ext"]

    def bool_mod(self, modoact):
        if modoact == "invierno":
            self.verano = False
            self.antihielo = False
            self.invierno = True
        elif modoact == "verano":

            self.antihielo = False
            self.invierno = False
            self.verano = True

        elif modoact == "antihielo":
            self.invierno = False
            self.verano = False
            self.antihielo = True

    def seguridad(self):
        reles.seguridad()

    def act_seguridades(self):
        with open('/home/pi/ASIGEO/json_f/seguridades.json', 'r') as file:
            seguridades = json.load(file)
        # seguridades
        if self.zona == 1:
            self.inv_tmax_agua = seguridades["inv_tmax_agua1"]
            self.inv_tmax_suelo = seguridades["inv_tmax_suelo1"]
            self.inv_tmin_suelo = seguridades["inv_tmin_suelo1"]
            self.ver_tmin_agua = seguridades["ver_tmin_agua1"]
            self.ver_tmin_suelo = seguridades["ver_tmin_suelo1"]
            self.ant_tmax_agua = seguridades["ant_tmax_agua1"]
            self.ant_tmin_agua = seguridades["ant_tmin_agua1"]
            self.ant_tmin_suelo = seguridades["ant_tmin_suelo1"]
        elif self.zona == 2:
            self.inv_tmax_agua = seguridades["inv_tmax_agua2"]
            self.inv_tmax_suelo = seguridades["inv_tmax_suelo2"]
            self.inv_tmin_suelo = seguridades["inv_tmin_suelo2"]
            self.ver_tmin_agua = seguridades["ver_tmin_agua2"]
            self.ver_tmin_suelo = seguridades["ver_tmin_suelo2"]
            self.ant_tmax_agua = seguridades["ant_tmax_agua2"]
            self.ant_tmin_agua = seguridades["ant_tmin_agua2"]
            self.ant_tmin_suelo = seguridades["ant_tmin_suelo2"]

        self.ant_tmin_ext = seguridades["ant_tmin_ext"]
        self.ver_tmin_ext = seguridades["ver_tmin_ext"]

    def logica(self, modo):
        print(self.sonda_exterior, self.sonda_ambiente, self.sonda_agua, self.sonda_suelo)
        self.bool_mod(modo)

        calor = self.invierno
        frio = self.verano
        antih = self.antihielo

        if calor and not frio and not antih:

            reles.relayon(8)  # Encender ZONA BAÑO

            tmaxAgua = self.sonda_agua > self.inv_tmax_agua
            tminSuelo = self.sonda_suelo < self.inv_tmin_suelo
            tmaxSuelo = self.sonda_suelo > self.inv_tmax_suelo
            seguridadmax = (calor and tmaxAgua) or (calor and tmaxSuelo)

            termostato = self.sonda_ambiente < self.consigna - self.grado_confort
            print("Termostato",self.zona,termostato)

            if self.modo_curva == 0:
                m = 1
                b = 40  # modo normal
            elif self.modo_curva == 1:
                m = 1.5
                b = 50  # modo intenso
            elif self.modo_curva == 2:
                m = 0.8
                b = 36  # modo reducido

            consigna = curva(self.sonda_exterior, b, m)
            diferencial = consigna - self.sonda_agua
            print("Curva= " + str(consigna))
            print("Diferencial= " + str(diferencial))

            pideLargo = diferencial > 6
            pideCorto = 1 < diferencial <= 6
            tempCorrecta = -1 <= diferencial <= 1
            excesoCalor = diferencial < -1

            # LOGICA DE APERTURAS
            B006 = termostato and not seguridadmax and pideLargo
            B012 = tminSuelo and not seguridadmax
            B007 = termostato and not seguridadmax and pideCorto
            B014 = B006 or B012  # activa Temporizacion larga
            B018 = B007 and not B014  # Activa temporizacion corta

            # LOGICA DE CIERRES
            B022 = not termostato and not tminSuelo
            B024 = excesoCalor and not tminSuelo
            B025 = B022 or B024 or seguridadmax  # ACTIVA TEMPORIZACION LARGA

            # Logica de parada
            B019 = tempCorrecta and not tminSuelo and not B025 and not (B014 or B018)  # Temperatura correcta

            if not self.modo_bomba or (self.modo_bomba and (B014 or B018)):
                reles.abrir_bomba(self.zona)
            else:
                reles.cerrar_bomba(self.zona)

            if B019:
                reles.parar_zona(self.zona)
                self.temporizador = 0
                sleep(5)
                self.funcionando = 0

            elif B014:
                reles.abrir_zona(self.zona)
                if self.funcionando == 2:  # antes estaba abriendo corto

                    self.temporizador = 0
                    # activo rele


                elif self.funcionando == 3:
                    self.temporizador = 0

                else:  # funcionando = 1 o funcionando = 0

                    self.temporizador += 1
                    if self.temporizador == self.TEMP_LARGA:
                        reles.parar_zona(self.zona)
                        self.temporizador = 0

                self.funcionando = 1
                sleep(5)

            elif B018:  # abrir corto
                reles.abrir_zona(self.zona)
                if self.funcionando == 1:  # antes estaba abriendo largo

                    self.temporizador = 0

                    # activo rele
                    #print("Abriendo")
                    sleep(5)

                elif self.funcionando == 3:

                    self.temporizador = 0
                    sleep(5)

                else:  # funcionando = 2 o 0

                    self.temporizador += 1
                    sleep(5)

                    if self.temporizador == self.TEMP_CORTA:

                        reles.parar_zona(self.zona)
                        sleep(5)
                        self.temporizador = 0


                self.funcionando = 2

            elif B025:  # Cerrar largo
                reles.cerrar_zona(self.zona)
                if (self.funcionando == 1) or (self.funcionando == 2):
                    #print("Paro abrir y empiezo a cerrar")  # cierro CH1 y abro CH2
                    self.temporizador = 0
                    sleep(5)
                else:  # Antes ya estaba cerrando o parado
                    #print("cerrando")
                    self.temporizador += 1
                    sleep(5)
                    if self.temporizador == 6:
                        reles.parar_zona(self.zona)  # paro de cerrar
                        print("Paro 5 seg")
                        sleep(5)
                        self.temporizador = 0
                        #print("Enciendo relee CH2")  # Abro relee CH2

                self.funcionando = 3


            else:
                print('La has liao primo')

        elif frio and not calor and not antih:  # modo verano

            reles.relayoff(8)

            tmin_ext = self.sonda_exterior < self.ver_tmin_ext
            tmin_agua = self.sonda_agua < self.ver_tmin_agua
            tmin_suelo = self.sonda_suelo < self.ver_tmin_suelo

            termostato = self.sonda_ambiente > self.consigna

            seg_verano = frio and (tmin_ext or tmin_agua or tmin_suelo)

            # LOGICA CIERRE

            cerrar = not termostato or seg_verano
            abrir = not seg_verano and termostato and not cerrar

            if not self.modo_bomba or (self.modo_bomba and abrir):
                reles.abrir_bomba(self.zona)
            else:
                reles.cerrar_bomba(self.zona)

            if cerrar:
                reles.cerrar_zona(self.zona)
                if (self.funcionando == 1) or (self.funcionando == 2):
                    print("Paro abrir y empiezo a cerrar")  # cierro CH1 y abro CH2
                    self.temporizador = 0
                    sleep(5)
                else:  # Antes ya estaba cerrando
                    #print("cerrando")

                    self.temporizador += 1
                    if self.temporizador == 6:
                        reles.parar_zona(self.zona)
                        print("Paro 5 seg")
                        sleep(5)
                        self.temporizador = 0
                        #print("Enciendo relee CH2")  # Abro relee CH2
                    else:
                        sleep(5)

                self.funcionando = 3


            elif abrir:
                reles.abrir_zona(self.zona)
                if self.funcionando == 1:  # antes estaba abriendo largo
                    print("Paro abriendo largo, abro corto")  # cambio temporizador
                    self.temporizador = 0

                    # activo rele
                    #print("Abriendo")
                    sleep(5)

                elif self.funcionando == 3:
                    #print("Paro cerrar, abro corto")  # cierro CH2, abro CH1
                    self.temporizador = 0
                    sleep(5)

                else:  # funcionando = 2

                    #print("Sigo abriendo")
                    self.temporizador += 1
                    if self.temporizador == self.TEMP_CORTA:
                        reles.parar_zona(self.zona)
                        #print("Paro relee")  # cierro relee CH1
                        sleep(5)
                        self.temporizador = 0
                        #print("Enciendo relee CH1")  # Abro relee CH1

                    else:
                        sleep(5)

                self.funcionando = 2

        elif antih and not calor and not frio:
            reles.relayoff(8)

            tmax_agua = self.sonda_agua > self.ant_tmax_agua
            tmin_agua = self.sonda_agua < self.ant_tmin_agua
            tmin_suelo = self.sonda_suelo < self.ant_tmin_suelo
            tmin_ext = self.sonda_exterior < self.ant_tmin_ext

            abrir = tmin_agua or (tmin_ext and not tmin_agua) or (tmin_suelo and not tmax_agua)

            if not self.modo_bomba or (self.modo_bomba and abrir):
                reles.abrir_bomba(self.zona)
            else:
                reles.cerrar_bomba(self.zona)

            if abrir:
                reles.abrir_zona(1)
                if self.funcionando == 3:
                    self.temporizador = 0
                    sleep(5)
                else:  # antes ya estaba abriendo
                    self.temporizador += 1
                    if self.temporizador == self.TEMP_CORTA:
                        reles.parar_zona(self.zona)
                        sleep(5)
                        self.temporizador = 0

                    else:
                        sleep(5)
                self.funcionando = 2


            else:
                reles.cerrar_zona(self.zona)
                if self.funcionando == 2:
                    self.temporizador = 0
                    sleep(5)
                else:  # antes ya estaba cerrando
                    self.temporizador += 1
                    if self.temporizador == self.TEMP_LARGA:
                        reles.parar_zona(self.zona)
                        sleep(5)
                        self.temporizador = 0

                    else:
                        sleep(5)
                self.funcionando = 3

        return self.funcionando


class ZonaDirecta:
    def __init__(self):
        self.modo = "invierno"
        self.invierno = True
        self.verano = False
        self.antihielo = False
        reles = Relees()
        self.consigna = 20
        self.sonda_ambiente = 20

    def bool_mod(self, modoact):
        if modoact == "invierno":
            self.verano = False
            self.antihielo = False
            self.invierno = True
        elif modoact == "verano":

            self.antihielo = False
            self.invierno = False
            self.verano = True

        elif modoact == "antihielo":
            self.invierno = False
            self.verano = False
            self.antihielo = True

    def logica(self, modo):
        print(self.sonda_exterior, self.sonda_ambiente, self.sonda_agua, self.sonda_suelo)
        self.bool_mod(modo)

        calor = self.invierno
        frio = self.verano
        antih = self.antihielo

        if calor:
            if self.consigna > self.sonda_ambiente:
                reles.abrir_bomba(3)
            else:
                reles.cerrar_bomba(3)

        elif frio:
            if self.consigna < self.sonda_ambiente:
                reles.abrir_bomba(3)
            else:
                reles.cerrar_bomba(3)

        sleep(5)
