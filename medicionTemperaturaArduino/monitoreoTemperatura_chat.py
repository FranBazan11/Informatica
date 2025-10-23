import threading
import RPi.GPIO as GPIO
import time
import os
import glob

# ----------------------- Declaramos ctes ----------------------------
# Generales
i = 0
promedio = 0
k = 0

# --------Leds--------
LedAmarillo = 17
LedRojo = 22
LedVerde = 27

GPIO.setmode(GPIO.BCM)
GPIO.setup(LedAmarillo,GPIO.OUT)
GPIO.setup(LedRojo,GPIO.OUT)
GPIO.setup(LedVerde,GPIO.OUT)

#------ Sensor ------
N = 5 #Cantidad de Ciclos para el promedio
Ultimos_N_eventos = [N]
frecuencia_de_ciclo = 1 # Cambiar a 3.5
ultimos_promedios = 0
promedio_anterior = 0
contador_de_promedios =0

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28-*')[0]
device_file = device_folder + '/w1_slave'

#------ Pulsador ------
BUTTON_GPIO = 3
Ciclo_Max = 10 # Tiempo máximo que el pulsador puede estar activado
Ciclo_min = 2.5 # Tiempo mínimo que el pulsador puede estar activado
Tiempo_salida = 1 # Tiempo para solicitar la salida del programa
Pulsacion_min = 1 # Límite de pulsación válida
Pulsacion_max = 10 # Límite superior
tiempo_mantenido = 0
apretado = 0

# ---------------- Declaramos variables----------------
press_time= None # Variable para guardar el tiempo que se pulsa
current_period = 2 # Periodo del ciclo inicial

#---------------- Funciones ----------------------------

#Sensor
#Devuelve lineas en crudo
def read_temp_raw():
    f= open(device_file,'r')
    lines = f.readlines()
    f.close()
    return lines

#Relee hasta la 1ra línea termine en YES
def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:]!='YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string)/1000
        return temp_c

#------ Pulsador ------
# Iniciamos el programa del pulsador
def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_GPIO,GPIO.IN)

def boton_presionado():
    global press_time
    tiempo_mantenido = 0
    control = 0
    press_time = time.time() # Comenzamos a medir el tiempo
    while (control == 0):
        #Calculamos el tiempo de medición
        #Titileo de leds
        time.sleep(1)
        GPIO.output(LedRojo,GPIO.HIGH)
        GPIO.output(LedVerde,GPIO.HIGH)
        GPIO.output(LedAmarillo,GPIO.HIGH)
        time.sleep(0.05)
        GPIO.output(LedRojo,GPIO.LOW)
        GPIO.output(LedVerde,GPIO.LOW)
        GPIO.output(LedAmarillo,GPIO.LOW)

        if (GPIO.input(BUTTON_GPIO) == 1):
            tiempo_mantenido = time.time() - press_time
            control = 1
    return tiempo_mantenido

#====================== BUCLE PRINCIPAL ======================

ultimo_ciclo = time.time()
while (k==0):

    ahora = time.time()
    if (ahora >= proxima_lectura):

        #Guardamos los nuevos valores de Ts
        temp = read_temp()
        #print(f"La temperatura medida es: {temp}")
        i= i+1
        Ultimos_N_eventos.append(temp)
        while (proxima_lectura <= ahora):
            proxima_lectura += frecuencia_de_ciclo

        #Buscamos promedio con las últimas N mediciones
        if (i>=N):
            suma = 0
            j = 0
            contador_de_promedios = contador_de_promedios + 1
            for j in range((1-N),1,1):
                suma = suma + Ultimos_N_eventos[j]
            promedio = suma/N
            print(f"El promedio de las últimas 5 mediciones es: {promedio}")

        setup_gpio()
        if (GPIO.input(BUTTON_GPIO) == 0):
            print("Botón presionado")
            apretado = boton_presionado() #Tiempo mantenido

        elif (apretado != 0):
            print("Se soltó el pulsador")
            print(f"Pulsación de {apretado} segundos detectada")

            if (apretado < Pulsacion_min): #Condición de apagado
                print("Pulsación menor a 1 segundo, finalizando el programa...")
                k = 1
            elif (apretado < Ciclo_min ):
                frecuencia_de_ciclo = Ciclo_min
                print(f"La nueva frecuencia de ciclo es: {frecuencia_de_ciclo}")
            elif (apretado < Pulsacion_max ): #Cambio de frecuencia a la frecuencia mínima
                frecuencia_de_ciclo = apretado
                print(f"La nueva frecuencia de ciclo es: {frecuencia_de_ciclo}")
            elif (apretado > Pulsacion_max): #Cambio de frecuencia a la frecuencia máxima
                frecuencia_de_ciclo = Ciclo_Max
                print(f"La nueva frecuencia de ciclo es: {frecuencia_de_ciclo} ")
                apretado = 0

        #--------------------LEDS-----------------------
        Desviacion = promedio*0.1
        if (contador_de_promedios == 0):
            GPIO.output(LedRojo,GPIO.HIGH)
            GPIO.output(LedVerde,GPIO.HIGH)
            GPIO.output(LedAmarillo,GPIO.HIGH)

        #print(f"La desviacion es: {Desviacion}")

        if (contador_de_promedios > 1):
            #print(f"La desviacion + promedio es: {promedio+Desviacion}")
            if (temp > (promedio+Desviacion)):
                GPIO.output(LedRojo,GPIO.HIGH)
                GPIO.output(LedAmarillo,GPIO.LOW)
                GPIO.output(LedVerde,GPIO.LOW)
                #print("Se prendió el rojo")

            elif(temp < (promedio-Desviacion)):
                GPIO.output(LedVerde,GPIO.HIGH)
                GPIO.output(LedRojo,GPIO.LOW)
                GPIO.output(LedAmarillo,GPIO.LOW)
                #print("Se prendió el verde")

            else:
                GPIO.output(LedAmarillo,GPIO.HIGH)
                GPIO.output(LedVerde,GPIO.LOW)
                GPIO.output(LedRojo,GPIO.LOW)
                #print("Se prendió el amarillo")