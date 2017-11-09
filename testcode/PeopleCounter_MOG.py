import time
import argparse
import datetime
import imutils
import math
import cv2
import numpy as np

width = 800

textIn = 0
textOut = 0

def testIntersectionIn(x, y):

    res = y - 250
    if((res >= -5) and  (res < 5)):
        print (str(res))
        return True
    return False



def testIntersectionOut(x, y):
    res = y - 275
    if ((res >= -5) and (res <= 5)):
        print (str(res))
        return True

    return False

cap = cv2.VideoCapture(0)

kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
fgbg = cv2.createBackgroundSubtractorMOG2()
fourcc = cv2.VideoWriter_fourcc(*'XVID')
frame1 = np.zeros((800,640))
out = cv2.VideoWriter("PeopleCounter.avi",fourcc, 5.0, np.shape(frame1))

while(1):
    ret, frame = cap.read()
    out.write(frame)
    fgmask = fgbg.apply(frame)
    (_,cnts, _) = cv2.findContours(fgmask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    maxArea = 0
    for c in cnts:
        Area = cv2.contourArea(c)
        if Area < maxArea :
        #if cv2.contourArea(c) < 500:
            (x, y, w, h) = (0,0,0,0)
            continue
        else:
            if Area < 5000:
                (x, y, w, h) = (0,0,0,0)
                continue
            else:
                maxArea = Area
                m=c
                (x, y, w, h) = cv2.boundingRect(m)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.line(frame, (0, 200), (width, 200), (250, 0, 1), 2) #blue line
        cv2.line(frame, (0, 250), (width, 250), (0, 0, 255), 2)#red line

        rectagleCenterPont = ((x + x + w) /2, (y + y + h) /2)
        cv2.circle(frame, rectagleCenterPont, 1, (0, 0, 255), 5)

        if(testIntersectionIn((x + x + w) / 2, (y + y + h) / 2)):
            textIn += 1

        if(testIntersectionOut((x + x + w) / 2, (y + y + h) / 2)):
            textOut += 1

    cv2.putText(frame, "In: {}".format(str(textIn)), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    cv2.putText(frame, "Out: {}".format(str(textOut)), (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
    cv2.imshow("Security Feed", frame)

    k = cv2.waitKey(30)&0xff
    if k==27:
        break
out.release()
cap.release()
cv2.destoryAllWindows()