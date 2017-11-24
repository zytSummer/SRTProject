import time
import argparse
import datetime
import imutils
import math
import cv2
import numpy as np
import threading

width = 800

class PeopleCounter(object):
    def __init__(self, cameraId = 1):
        self.cameraId = cameraId
        self.originNum = 0
        self.inNum = 0
        self.outNum = 0
        self.totleNum = 0
        self.alive = True
        self.InDelayTime = 0
        self.OutDelayTime = 0
        #self.CvOpen()
        #self.PeopleCounterProc()
    def CvOpen(self):
        self.cap = cv2.VideoCapture(self.cameraId)
        self.alive = True
    def PeopleCounterProc(self):
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
        fgbg = cv2.createBackgroundSubtractorMOG2()
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        frame1 = np.zeros((640,480))
        self.out = cv2.VideoWriter(datetime.datetime.now().strftime("%A_%d_%B_%Y_%I_%M_%S%p")+'.avi',fourcc, 5.0, np.shape(frame1))
        Area = 0
        while(self.alive):
            ret, frame = self.cap.read()
            self.out.write(frame)
            frame = imutils.resize(frame, width=width)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            cv2.imshow("gray", gray)
            thresh = fgbg.apply(gray)
            thresh = cv2.threshold(thresh, 200, 255, cv2.THRESH_BINARY)[1]
            fgmask = cv2.dilate(thresh, None, iterations=2)
            cv2.imshow("fgmask window", fgmask)
            (_,cnts, _) = cv2.findContours(fgmask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            maxArea = 0
            for c in cnts:
                Area = cv2.contourArea(c)
                if Area < maxArea :
                #if cv2.contourArea(c) < 500:
                    (x, y, w, h) = (0,0,0,0)
                    continue
                else:
                    if Area < 7000:
                        (x, y, w, h) = (0,0,0,0)
                        continue
                    else:
                        maxArea = Area
                        m=c
                        (x, y, w, h) = cv2.boundingRect(m)
                        
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                cv2.line(frame, (0, 300), (width, 300), (250, 0, 1), 2) #blue line
                cv2.line(frame, (0, 250), (width, 250), (0, 0, 255), 2) #red line

                rectagleCenterPont = ((x + x + w) /2, (y + y + h) /2)
                cv2.circle(frame, rectagleCenterPont, 1, (0, 0, 255), 5)
#                if (self.InDelayTime > 0) or (self.OutDelayTime > 0):
#                    self.InDelayTime -= 1
#                else:
                if(self.testIntersectionIn((x + x + w) / 2, (y + y + h) / 2)):
                    self.inNum += 1

#                if (self.OutDelayTime > 0) or (self.InDelayTime > 0):
#                    self.OutDelayTime -= 1
#                else:
                if(self.testIntersectionOut((x + x + w) / 2, (y + y + h) / 2)):
                    self.outNum += 1
                self.totleNum = self.originNum + self.inNum - self.outNum
                #self.out.write(frame)
	
            cv2.putText(frame, "In: {}".format(str(self.inNum)), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv2.putText(frame, "Out: {}".format(str(self.outNum)), (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv2.putText(frame, "area: {}".format(str(Area)), (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
            cv2.imshow("SRT Window", frame)

            k = cv2.waitKey(30)&0xff
            if k==27:
                break
        self.CvClose()
    def CvClose(self):
        self.alive = False
        self.out.release()
        self.cap.release()
        cv2.destroyAllWindows()

    def testIntersectionIn(self, x, y):
        res = y - 300
        if((res >= -10) and (res < 10)):
#            self.InDelayTime = 10
            print "In:",(str(res))
            return True
        return False

    def testIntersectionOut(self, x, y):
        res = y - 250
        if ((res >= -10) and (res <= 10)):
#            self.OutDelayTime = 10
            print "out:",(str(res))
            return True
        return False

if __name__ == '__main__':
    counter = PeopleCounter(0)
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
        #print "input num: ", counter.inNum, "output num: ", counter.outNum