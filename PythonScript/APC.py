import os
import serial
import cv2
import numpy as np
from keras.models import load_model
from keras.preprocessing.image import img_to_array
import time
import serial.tools.list_ports
import threading

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

ports = serial.tools.list_ports.comports()

for port, desc, hwid in sorted(ports):
    print(f"{port}: {desc} [{hwid}]")

# ConfiguraziJ4one della porta seriale
port = 'COM13'
baudrate = 57600

try:
    print ("Configuro la porta seriale...")
    ser = serial.Serial(port, baudrate, timeout=1)
    print("Porta seriale aperta: ", port)


    print ("Carico il modello...")
    model1=load_model(os.path.join(SCRIPT_DIR, 'model15.h5'))
    print ("Modello caricato")

    print ("Carico i classificatori...")
    face_classifier=cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml')
    left_eye_classifier = cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_lefteye_2splits.xml')
    right_eye_classifier =cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_righteye_2splits.xml')

    print ("Definisco la predizione...")
    IMG_SIZE=24
    closed_start_time = None
    flag1,flag2,flag3,flag4,flag5,flag6=0,0,0,0,0,0

    def predict(img, model):
        image = cv2.resize(img, (IMG_SIZE,IMG_SIZE))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image = image.astype("float") / 255.0
        image = img_to_array(image)
        image = np.expand_dims(image, axis=0)    
        prediction = model.predict(image)[0]
        if prediction < 0.3:
            prediction = 'closed'
        elif prediction > 0.6:
            prediction = 'open'
        return prediction
    
    print ("Funzione per leggere i dati da STM32")
    def serial_reader(ser):
        while True:
            if ser.in_waiting > 0:
                message = ser.readline().decode('utf-8').rstrip()
                print("Messaggio dalla porta seriale:", message)

    print ("Avvio la predizione...")
    cap = cv2.VideoCapture(0)

    # Avvio del thread per leggere dalla porta seriale
    serial_thread = threading.Thread(target=serial_reader, args=(ser,), daemon=True)
    serial_thread.start()

    while True:

        '''
        # Leggi l'input da tastiera
        key_press = input("Premi un tasto: ")

        # Invia il carattere digitato alla porta seriale
        ser.write(key_press.encode('utf-8'))
        '''

        
        ret, frame=cap.read()
        if ret:        
            frame = cv2.resize(frame, (0, 0), fx=0.6, fy=0.6)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces=face_classifier.detectMultiScale(gray,1.3,5)
            for (x,y,w,h) in faces:
                left_face = frame[y:y+h, x+int(w/2):x+w]
                left_face_gray = gray[y:y+h, x+int(w/2):x+w]
                
                right_face = frame[y:y+h, x:x+int(w/2)]
                right_face_gray = gray[y:y+h, x:x+int(w/2)]

                left_eye = left_eye_classifier.detectMultiScale(left_face_gray,scaleFactor=1.1,minNeighbors=5,minSize=(30, 30),flags = cv2.CASCADE_SCALE_IMAGE)

                right_eye =right_eye_classifier.detectMultiScale(right_face_gray,scaleFactor=1.1,minNeighbors=5,minSize=(30, 30),flags = cv2.CASCADE_SCALE_IMAGE)

                    
                for (ex,ey,ew,eh) in right_eye:
                    pred = predict(right_face[ey:ey+eh,ex:ex+ew],model1)

                    if pred=='closed':
                        flag1=1

                    elif pred=='open':
                        flag2=1
                        
                for (ex,ey,ew,eh) in left_eye:
                    pred = predict(left_face[ey:ey+eh,ex:ex+ew],model1)
                    if pred=='closed':
                        flag3=1
                    elif pred=='open':
                        flag4=1
                
                #Entrambi chiusi
                if flag1==1 and flag3==1:
                    cv2.putText(frame,'Closed', (10, 50), cv2.FONT_HERSHEY_SIMPLEX,0.75, (255, 255, 0), 2)
                    # Invia i dati alla porta seriale
                    #ser.write('C'.encode('utf-8'))
                    if closed_start_time is None:
                        closed_start_time = time.time()  # Aggiunto: inizio del timer
                    elif time.time() - closed_start_time >= 2.0:  # Modificato: tempo di chiusura 1.5 secondi
                        ser.write('A'.encode('utf-8')) #ALLERT
                        closed_start_time = None  # Reset del timer 
                    flag1=0 
                    flag3=0
                    flag5=1
                
                #entrambi aperti
                elif flag2==1 and flag4==1:
                    closed_start_time = None  # Reset del timer 
                    cv2.putText(frame,'Open', (10, 200), cv2.FONT_HERSHEY_SIMPLEX,0.75, (255, 255, 0), 2)
                    ser.write('O'.encode('utf-8'))
                    flag2=0
                    flag4=0
                    flag6=1
                    
                #blinking
                if flag5==1 and flag6==1:
                    cv2.putText(frame,'********Blink*******', (50, 150), cv2.FONT_HERSHEY_SIMPLEX,0.75, (0, 255, 255), 2)
                    #ser.write('B'.encode('utf-8'))
                    flag5=0
                    flag6=0
                    
            cv2.imshow('Live face dectector',frame)
        if cv2.waitKey(1)==13:
            break
        
    cap.release()
    cv2.destroyAllWindows()
    
    
except serial.SerialException as e:
    print(f"Errore di connessione alla porta {port}: {e}")



