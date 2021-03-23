from time import sleep


# funcionando = 1 abriendo largo
# funcionando = 2 abriendo corto
# funcionando = 3 cerrando largo


def curva(x, b, m):
    y = b - m * x
    return y


class LogicaZona:
    TEMP_LARGA = 6
    TEMP_CORTA = 2

    def __init__(self, zona):
        self.zona = zona

        self.temporizador = 0
        self.modo_bomba = False  # False = Continua  True = Termostato
        self.grado_confort = 0
        self.modo_curva = 0  # 0 modo normal #1 modo intenso # 2 reducido
        self.consigna = 20
        self.sonda_exterior = 0
        self.sonda_ambiente = 0
        self.sonda_agua = 0
        self.sonda_suelo = 0
        self.funcionando = 0
        self.invierno = True
        self.verano = False
        self.antihielo = False

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
        print(modo)
        self.bool_mod(modo)
        calor = self.invierno
        frio = self.verano
        antih = self.antihielo


        if calor and not frio and not antih:
            tmaxAgua = self.sonda_agua > 52
            tminSuelo = self.sonda_suelo < 22
            tmaxSuelo = self.sonda_suelo > 30
            seguridadmax = (calor and tmaxAgua) or (calor and tmaxSuelo)

            termostato = self.sonda_ambiente < self.consigna - self.grado_confort

            if self.modo_curva == 0:
                m = 1;
                b = 40  # modo normal
            elif self.modo_curva == 1:
                m = 1.5;
                b = 50  # modo intenso
            elif self.modo_curva == 2:
                m = 0.8;
                b = 36  # modo reducido

            consigna = curva(self.sonda_exterior, b, m)
            diferencial = consigna - self.sonda_agua

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
            B019 = tempCorrecta and not tminSuelo
            B022 = not termostato and not tminSuelo
            B024 = excesoCalor and not tminSuelo
            B025 = B019 or B022 or B024 or seguridadmax  # ACTIVA TEMPORIZACION LARGA

            if not self.modo_bomba or (self.modo_bomba and (B014 or B018)):
                print("Abro bomba " + str(self.zona))
            else:
                print("Cierro bomba " + str(self.zona))

            if B014:
                print("Abro Zona " + str(self.zona))
                if self.funcionando == 2:  # antes estaba abriendo corto
                    print("Paro abriendo corto, abro largo")  # cambio temporizador

                    self.temporizador = 0
                    # activo rele
                    print("Abriendo")

                elif self.funcionando == 3:
                    print("Paro cerrar, abro largo")  # cierro CH2, abro CH1
                    self.temporizador = 0
                    print("Abriendo")

                else:  # funcionando = 1
                    print("Sigo abriendo")
                    self.temporizador += 1
                    if self.temporizador == self.TEMP_LARGA:
                        print("Paro zona " + str(self.zona))
                        sleep(5)
                        self.temporizador = 0

                self.funcionando = 1
                sleep(5)

            elif B018:  # abrir corto
                print("Abro Zona " + str(self.zona))
                if self.funcionando == 1:  # antes estaba abriendo largo
                    print("Paro abriendo largo, abro corto")  # cambio temporizador
                    self.temporizador = 0

                    # activo rele
                    print("Abriendo")
                    sleep(5)

                elif self.funcionando == 3:
                    print("Paro cerrar, abro corto")  # cierro CH2, abro CH1
                    self.temporizador = 0
                    sleep(5)

                else:  # funcionando = 2
                    print("Sigo abriendo")
                    self.temporizador += 1
                    sleep(5)

                    if self.temporizador == self.TEMP_CORTA:
                        print("Paro zona " + str(self.zona))
                        sleep(5)
                        self.temporizador = 0

                self.funcionando = 2

            elif B025:  # Cerrar largo
                print("Cierro zona " + str(self.zona))
                if (self.funcionando == 1) or (self.funcionando == 2):
                    print("Paro abrir y empiezo a cerrar")  # cierro CH1 y abro CH2
                    self.temporizador = 0
                    sleep(5)
                else:  # Antes ya estaba cerrando
                    print("cerrando")
                    self.temporizador += 1
                    sleep(5)
                    if self.temporizador == 6:
                        print("Paro zona " + str(self.zona))

                        sleep(5)
                        self.temporizador = 0

                self.funcionando = 3


            else:
                print('La has liao primo')

        elif frio and not calor and not antih:  # modo verano
            tmin_ext = self.sonda_exterior < 20
            tmin_agua = self.sonda_agua < 15
            tmin_suelo = self.sonda_suelo < 17.5
            termostato = self.sonda_ambiente > self.consigna

            seg_verano = frio and (tmin_ext or tmin_agua or tmin_suelo)

            # LOGICA CIERRE

            cerrar = not termostato or seg_verano
            abrir = not seg_verano and termostato and not cerrar

            if not self.modo_bomba or (self.modo_bomba and abrir):
                print("Abro bomba " + str(self.zona))
            else:
                print("Cierro bomba " + str(self.zona))

            if cerrar:
                print("Cierro Zona " + str(self.zona))
                if (self.funcionando == 1) or (self.funcionando == 2):

                    self.temporizador = 0
                    sleep(5)
                else:  # Antes ya estaba cerrando
                    print("cerrando")

                    self.temporizador += 1
                    if self.temporizador == 6:
                        print("Paro zona " + str(self.zona))
                        sleep(5)
                        self.temporizador = 0

                    else:
                        sleep(5)

                self.funcionando = 3

            elif abrir:
                print("Abro zona " + str(self.zona))
                if self.funcionando == 1:  # antes estaba abriendo largo
                    print("Paro abriendo largo, abro corto")  # cambio temporizador
                    self.temporizador = 0
                    sleep(5)

                elif self.funcionando == 3:
                    print("Paro cerrar, abro corto")  # cierro CH2, abro CH1
                    self.temporizador = 0
                    sleep(5)

                else:  # funcionando = 2

                    print("Sigo abriendo")
                    self.temporizador += 1
                    if self.temporizador == self.TEMP_CORTA:
                        print("Paro zona " + str(self.zona))
                        sleep(5)
                        self.temporizador = 0


                    else:
                        sleep(5)

                self.funcionando = 2

        elif antih and not calor and not frio:

            tmax_agua = self.sonda_agua > 30
            tmin_agua = self.sonda_agua < 5
            tmin_suelo = self.sonda_suelo < 8
            tmin_ext = self.sonda_exterior < 5

            abrir = tmin_agua or (tmin_ext and not tmin_agua) or (tmin_suelo and not tmax_agua)

            if not self.modo_bomba or (self.modo_bomba and abrir):
                print("Abro bomba " + str(self.zona))
            else:
                print("Cierro bomba " + str(self.zona))

            if abrir:
                print("Abro zona " + str(self.zona))
                if self.funcionando == 3:
                    self.temporizador = 0
                    sleep(5)
                else:  # antes ya estaba abriendo
                    self.temporizador += 1
                    if self.temporizador == self.TEMP_CORTA:
                        print("Paro zona " + str(self.zona))
                        sleep(5)
                        self.temporizador = 0

                    else:
                        sleep(5)
                self.funcionando = 2


            else:
                print("Cierro zona " + str(self.zona))
                if self.funcionando == 2:
                    self.temporizador = 0
                    sleep(5)
                else:  # antes ya estaba cerrando
                    self.temporizador += 1
                    if self.temporizador == self.TEMP_LARGA:
                        print("Paro zona " + str(self.zona))
                        sleep(5)
                        self.temporizador = 0

                    else:
                        sleep(5)
                self.funcionando = 3

        return self.funcionando
