##Contador de personas
##Federico Mejia
import numpy as np
import cv2
import Person
import threading
import time
import datetime

class PeopleCounter(object):
    def __init__(self, cameraId = 1):
        self.cameraId = cameraId
        #define the in and out count
        self.originNum = 0
        self.outNum   = 0
        self.inNum = 0
        self.totleNum = 0
        #video status
        self.alive = True

    def AreaTHInit(self):
        self.width = self.cap.get(3)
        self.high = self.cap.get(4)
        self.frameArea = self.high*self.width
        self.areaTH_min = self.frameArea/50
        self.areaTH_double = self.frameArea/25
        self.areaTH_max = self.frameArea/10
        print 'Mini Area Threshold', self.areaTH_min
        print 'Max Area Threshold', self.areaTH_max
        print 'Double people Area Threshold', self.areaTH_double
    def LineInit(self):
        #Lines of entry/enter
        self.line_up = int(2*(self.high/5))
        self.line_down   = int(3*(self.high/5))
        
        self.up_limit =   int(1*(self.high/5))
        self.down_limit = int(4*(self.high/5))

        print "Red line y:",str(self.line_down)
        print "Blue line y:", str(self.line_up)
        
        self.line_down_color = (255,0,0)
        self.line_up_color = (0,0,255)
        pt1 =  [0, self.line_down];
        pt2 =  [self.width, self.line_down];
        self.pts_L1 = np.array([pt1,pt2], np.int32)
        self.pts_L1 = self.pts_L1.reshape((-1,1,2))
        pt3 =  [0, self.line_up];
        pt4 =  [self.width, self.line_up];
        self.pts_L2 = np.array([pt3,pt4], np.int32)
        self.pts_L2 = self.pts_L2.reshape((-1,1,2))

        pt5 =  [0, self.up_limit];
        pt6 =  [self.width, self.up_limit];
        self.pts_L3 = np.array([pt5,pt6], np.int32)
        self.pts_L3 = self.pts_L3.reshape((-1,1,2))
        pt7 =  [0, self.down_limit];
        pt8 =  [self.width, self.down_limit];
        self.pts_L4 = np.array([pt7,pt8], np.int32)
        self.pts_L4 = self.pts_L4.reshape((-1,1,2))

    def CvOpen(self):
        self.cap = cv2.VideoCapture(self.cameraId)
        if self.cap.isOpened():
            self.alive = True
            self.AreaTHInit()
            self.LineInit()
        #Imprime las propiedades de captura a consola
        #for i in range(19):
            #    print i, self.cap.get(i)
    def PeopleCounterProc(self):
        #Substractor de fondo
        
        fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows = True)

        #Elementos estructurantes para filtros morfoogicos
        kernelOp = np.ones((3,3),np.uint8)
        kernelOp2 = np.ones((5,5),np.uint8)
        kernelCl = np.ones((11,11),np.uint8)

        #Variables
        font = cv2.FONT_HERSHEY_SIMPLEX
        persons = []
        max_p_age = 5
        pid = 1

        while(self.alive):
        ##for image in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
            #Lee una imagen de la fuente de video
            ret, frame = self.cap.read()
        ##    frame = image.array

            for i in persons:
                i.age_one() #age every person one frame
            #########################
            #   PRE-PROCESAMIENTO   #
            #########################
            
            #Aplica substraccion de fondo
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame_gray = cv2.GaussianBlur(frame_gray, (21, 21), 0)
            fgmask = fgbg.apply(frame)
            fgmask2 = fgbg.apply(frame)
            cv2.imshow("fgmask2",fgmask2)

            #Binariazcion para eliminar sombras (color gris)
            try:
                ret,imBin= cv2.threshold(fgmask,200,255,cv2.THRESH_BINARY)
                ret,imBin2 = cv2.threshold(fgmask2,200,255,cv2.THRESH_BINARY)
                #Opening (erode->dilate) para quitar ruido.
                mask = cv2.morphologyEx(imBin, cv2.MORPH_OPEN, kernelOp)
                mask2 = cv2.morphologyEx(imBin2, cv2.MORPH_OPEN, kernelOp)
                cv2.imshow("Open mask2",mask2)
                #Closing (dilate -> erode) para juntar regiones blancas.
                mask =  cv2.morphologyEx(mask , cv2.MORPH_CLOSE, kernelCl)
                mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernelCl)
                cv2.imshow("Close mask2",mask2)
            except:
                print('EOF')
                print 'UP:',self.outNum
                print 'DOWN:',self.inNum
                break
            #################
            #   CONTORNOS   #
            #################
            
            # RETR_EXTERNAL returns only extreme outer flags. All child contours are left behind.
            _, contours0, hierarchy = cv2.findContours(mask2,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours0:
                area = cv2.contourArea(cnt)
                if (area > self.areaTH_min) and (area < self.areaTH_max):
                    #################
                    #   TRACKING    #
                    #################
                    
                    #Falta agregar condiciones para multipersonas, salidas y entradas de pantalla.
                    
                    M = cv2.moments(cnt)
                    cx = int(M['m10']/M['m00'])
                    cy = int(M['m01']/M['m00'])
                    x,y,width_cont,high_cont = cv2.boundingRect(cnt)

                    new = True
                    if cy in range(self.up_limit,self.down_limit):
                        for i in persons:
                            if abs(cx-i.getX()) <= width_cont and abs(cy-i.getY()) <= high_cont:
                                # el objeto esta cerca de uno que ya se detecto antes
                                # if the finded object near the old one, don't create a new person
                                new = False
                                i.updateCoords(cx,cy)   #actualiza coordenadas en el objeto and resets age
                                if i.going_UP(self.line_down,self.line_up) == True:
                                    if area > self.areaTH_double:
                                        self.outNum += 2;
                                    else:
                                        self.outNum += 1;
                                    print "ID:",i.getId(),'crossed going up at',time.strftime("%c")
                                    print "ID:",i.getId(),"crossed going up area = ",area
                                elif i.going_DOWN(self.line_down,self.line_up) == True:
                                    if area > self.areaTH_double:
                                        self.inNum += 2;
                                    else:
                                        self.inNum += 1;
                                    print "ID:",i.getId(),'crossed going down at',time.strftime("%c")
                                    print "ID:",i.getId(),"crossed going down area = ",area
                                self.totleNum = self.originNum + self.inNum - self.outNum
                                break
                            if i.getState() == '1':
                                if i.getDir() == 'down' and i.getY() > self.down_limit:
                                    i.setDone()
                                elif i.getDir() == 'up' and i.getY() < self.up_limit:
                                    i.setDone()
                            if i.timedOut():
                                #sacar i de la lista persons
                                index = persons.index(i)
                                persons.pop(index)
                                del i     #liberar la memoria de i
                        if new == True:
                            p = Person.MyPerson(pid,cx,cy, max_p_age)
                            persons.append(p)
                            pid += 1     
                    #################
                    #   DIBUJOS     #
                    #################
                    cv2.circle(frame,(cx,cy), 5, (0,0,255), -1)
                    img = cv2.rectangle(frame,(x,y),(x+width_cont,y+high_cont),(0,255,0),2)            
                    #cv2.drawContours(frame, cnt, -1, (0,255,0), 3)
                    
            #END for cnt in contours0
                    
            #########################
            # DIBUJAR TRAYECTORIAS  #
            #########################
            for i in persons:
        ##        if len(i.getTracks()) >= 2:
        ##            pts = np.array(i.getTracks(), np.int32)
        ##            pts = pts.reshape((-1,1,2))
        ##            frame = cv2.polylines(frame,[pts],False,i.getRGB())
        ##        if i.getId() == 9:
        ##            print str(i.getX()), ',', str(i.getY())
                cv2.putText(frame, str(i.getId()),(i.getX(),i.getY()),font,0.3,i.getRGB(),1,cv2.LINE_AA)
                
            #################
            #   IMAGANES    #
            #################
            str_up = 'UP: '+ str(self.outNum)
            str_down = 'DOWN: '+ str(self.inNum)
            frame = cv2.polylines(frame,[self.pts_L1],False,self.line_down_color,thickness=2)
            frame = cv2.polylines(frame,[self.pts_L2],False,self.line_up_color,thickness=2)
            frame = cv2.polylines(frame,[self.pts_L3],False,(255,255,255),thickness=1)
            frame = cv2.polylines(frame,[self.pts_L4],False,(255,255,255),thickness=1)
            cv2.putText(frame, str_up ,(10,40),font,0.5,(255,255,255),2,cv2.LINE_AA)
            cv2.putText(frame, str_up ,(10,40),font,0.5,(0,0,255),1,cv2.LINE_AA)
            cv2.putText(frame, str_down ,(10,90),font,0.5,(255,255,255),2,cv2.LINE_AA)
            cv2.putText(frame, str_down ,(10,90),font,0.5,(255,0,0),1,cv2.LINE_AA)
            cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
            cv2.imshow('Frame',frame)
            #cv2.imshow('Mask',mask)    
            
            #preisonar ESC para salir
            k = cv2.waitKey(30) & 0xff
            if k == 27:
                break
    def CvClose(self):
        self.alive = False
        self.out.release()
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    counter = PeopleCounter("Friday.avi")
    counter.CvOpen()
    print "Open OK"
    thread_peopleCounter = threading.Thread(target = counter.PeopleCounterProc)
    thread_peopleCounter.setDaemon(True)
    thread_peopleCounter.start()
    for i in range(0,10000):
        time.sleep(5)
        k = input()&0xff
        if k==27:
            break
        print "input num: ", counter.inNum, "output num: ", counter.outNum