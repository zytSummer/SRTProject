#! /usr/bin/env python
# -*- coding: utf-8 -*-

'''
Serial设备通讯帮助类
'''
__author__ = "jakey.chen"
__info__ = "Alex Zhang modified from jakey chen"
__version__ = "v2.0"

import sys
import threading
import time
import serial
import binascii
import logging
import Crc16

class SerialHelper(object):
    def __init__(self, Port="COM2", BaudRate="9600", ByteSize="8", Parity="N", Stopbits="1"):
        '''
        初始化一些参数
        '''
        self.l_serial = None
        self.alive = False
        self.port = Port
        self.baudrate = BaudRate
        self.bytesize = ByteSize
        self.parity = Parity
        self.stopbits = Stopbits
        self.thresholdValue = 64
        self.receive_data = ""

    def start(self):
        '''
        开始，打开串口
        '''
        self.l_serial = serial.Serial()
        self.l_serial.port = self.port
        self.l_serial.baudrate = self.baudrate
        self.l_serial.bytesize = int(self.bytesize)
        self.l_serial.parity = self.parity
        self.l_serial.stopbits = int(self.stopbits)
        self.l_serial.timeout = 2
        
        try:
            self.l_serial.open()
            if self.l_serial.isOpen():
                self.alive = True
        except Exception as e:
            self.alive = False
            logging.error(e)

    def stop(self):
        '''
        结束，关闭串口
        '''
        self.alive = False
        if self.l_serial.isOpen():
            self.l_serial.close()

    def read(self):
        '''
        循环读取串口发送的数据
        '''
        while self.alive:
            try:
                number = self.l_serial.inWaiting()
                if number:
                    self.receive_data += self.l_serial.read(number).replace(binascii.unhexlify("00"), "00")
                    if self.thresholdValue <= len(self.receive_data):
                        self.receive_data = ""
            except Exception as e:
                logging.error(e)

    def write(self, data, isHex=True):
        '''
        发送数据给串口设备
        '''
        self.crc = Crc16.crc16()
        if self.alive:
            if self.l_serial.isOpen():
                if isHex:
                    data = data.replace(" ", "").replace("\n", "")
                    print "enter write data = ", data
                    data = binascii.unhexlify(data)
                    print "Helper data ", data
                    #data_temp = self.crc.createarray_hex(data)
                self.l_serial.write(data)

                
if __name__ == '__main__':
    import threading
    ser = SerialHelper()
    ser.start()

    ser.write("123", isHex=False)
    thread_read = threading.Thread(target=ser.read)
    thread_read.setDaemon(True)
    thread_read.start()
    import time
    time.sleep(25)
    ser.stop()