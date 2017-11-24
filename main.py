#! /usr/bin/env python
# -*- coding: utf-8 -*-

import time
import datetime
import threading
import binascii
import platform
import logging

from UI import SerialTool
from COM import SerialHelper
from COM import PeopleCounter_MOG2
from COM import Crc16

if platform.system() == "Windows":
    from  serial.tools import list_ports
elif platform.system() == "Linux":
    import glob, os, re

import Tkinter as tk
import ttk

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')

class MainSerialToolUI(SerialTool.SerialToolUI):
    def __init__(self, master=None):
        super(MainSerialToolUI, self).__init__()
        self.ser = None
        self.receive_count = 0
        self.receive_data = ""
        self.send_data = ""
        self.send_data_crc = ""
        self.list_box_serial = list()
        self.find_all_serial()

    def __del__(self):
        if platform.system() == "Linux":
            try:
                self.ser.SetStopEvent()
            except:
                pass

    def find_all_serial(self):
        '''
        获取到串口列表
        '''
        if platform.system() == "Windows":
            try:
                self.temp_serial = list()
                for com in list_ports.comports():
                    strCom = com[0] + ": " + com[1][:-7].decode("gbk").encode("utf-8")
                    self.temp_serial.append(strCom)
                for item in self.temp_serial:
                    if item not in self.list_box_serial:
                        self.frm_left_listbox.insert("end", item)
                for item in self.list_box_serial:
                    if item not in self.temp_serial:
                        index = list(self.frm_left_listbox.get(0, self.frm_left_listbox.size())).index(item)
                        self.frm_left_listbox.delete(index)

                self.list_box_serial = self.temp_serial

                self.thread_findserial = threading.Timer(1, self.find_all_serial)
                self.thread_findserial.setDaemon(True)
                self.thread_findserial.start()
            except Exception as e:
                logging.error(e)
        elif platform.system() == "Linux":
            try:
                self.temp_serial = list()
                self.temp_serial = self.find_usb_tty()
                for item in self.temp_serial:
                    if item not in self.list_box_serial:
                        self.frm_left_listbox.insert("end", item)
                for item in self.list_box_serial:
                    if item not in self.temp_serial:
                        index = list(self.frm_left_listbox.get(0, self.frm_left_listbox.size())).index(item)
                        self.frm_left_listbox.delete(index)
                self.list_box_serial = self.temp_serial

                self.thread_findserial = threading.Timer(1, self.find_all_serial)
                self.thread_findserial.setDaemon(True)
                self.thread_findserial.start()
            except Exception as e:
                logging.error(e)

    def Toggle(self):
        '''
        打开关闭串口
        '''
        if self.frm_left_btn["text"] == "Open":
            try:
                self.currentStrCom = self.frm_left_listbox.get(self.frm_left_listbox.curselection())
                if platform.system() == "Windows":
                    self.port = self.currentStrCom.split(":")[0]
                elif platform.system() == "Linux":
                    self.port = self.currentStrCom
                self.baudrate = self.frm_left_combobox_baudrate.get()
                self.parity = self.frm_left_combobox_parity.get()
                self.databit = self.frm_left_combobox_databit.get()
                self.stopbit = self.frm_left_combobox_stopbit.get()
                self.cameraId = self.frm_left_combobox_cameraId.get()
                self.ser = SerialHelper.SerialHelper(Port=self.port,
                                                     BaudRate=self.baudrate,
                                                     ByteSize=self.databit,
                                                     Parity=self.parity,
                                                     Stopbits=self.stopbit)
                self.ser.start()
                if self.ser.alive:
                    self.frm_status_label["text"] = "Open [{0}] Successful!".format(self.currentStrCom)
                    self.frm_status_label["fg"] = "#66CD00"
                    self.frm_left_btn["text"] = "Close"
                    self.frm_left_btn["bg"] = "#F08080"

                    self.thread_read = threading.Thread(target=self.SerialRead)
                    self.thread_read.setDaemon(True)
                    self.thread_read.start()
                self.counter = PeopleCounter_MOG2.PeopleCounter(int(self.cameraId))
                self.counter.CvOpen()
                self.thread_peopleCounter = threading.Thread(target=self.counter.PeopleCounterProc)
                self.thread_peopleCounter.setDaemon(True)
                self.thread_peopleCounter.start()
            except Exception as e:
                logging.error(e)
                try:
                    self.frm_status_label["text"] = "Open [{0}] Failed!".format(self.currentStrCom)
                    self.frm_status_label["fg"] = "#DC143C"
                except Exception as ex:
                    logging.error(ex)

        elif self.frm_left_btn["text"] == "Close":
            try:
                self.ser.stop()
                self.receive_count = 0
            except Exception as e:
                logging.error(e)
            self.frm_left_btn["text"] = "Open"
            self.frm_left_btn["bg"] = "#008B8B"
            self.frm_status_label["text"] = "Close Serial Successful!"
            self.frm_status_label["fg"] = "#8DEEEE"
            self.counter.CvClose()

    def Open(self, event):
        '''
        双击列表打开/关闭串口
        '''
        self.Toggle()

    def Clear(self):
        self.frm_right_receive.delete("0.0", "end")
        self.receive_count = 0

    def Send(self):
        '''
        向已打开的串口发送数据
        如果为Hex发送，示例："31 32 33" [即为字符串 "123"]
        '''
        if self.ser:
        #判断是否进入测试模式，如果进入测试模式，则发送测试框中的内容
            if self.test_mode_cbtn_var.get() == 1:
                try:
                    # 发送新行
                    if self.new_line_cbtn_var.get() == 0:
                        test_send_data = str(self.frm_right_send.get("0.0", "end").encode("gbk")).strip()
                    else:
                        test_send_data = str(self.frm_right_send.get("0.0", "end")).strip() + "\r\n"  
                    
                    logging.info(self.space_b2a_hex(test_send_data))

                    # 是否十六进制发送
                    if self.send_hex_cbtn_var.get() == 1:
                        self.ser.write(test_send_data, isHex=True)
                    else:
                        self.ser.write(test_send_data)
                except Exception as e:
                    self.frm_right_receive.insert("end", str(e) + "\n")
                    logging.error(e)
            else:
            #测试模式下，Send按钮应无效
                self.frm_right_send.insert("end", self.send_data + "\n")
                self.frm_right_send.see("end")
                self.receive_send = ""

    def SerialRead(self):
        '''
        线程读取串口发送的数据
        '''
        while self.ser.alive:
            try:
                time.sleep(0.1)
                n = self.ser.l_serial.inWaiting()
                if n:
                    self.receive_data += self.ser.l_serial.read(n)#.replace(binascii.unhexlify("00"), "")
                    if self.thresholdValue <= len(self.receive_data) or ("\r\n" in self.receive_data):
                        self.receive_count += 1
                        # 接收显示是否为Hex
                        #print "Check recieve\n"
                        if self.receive_hex_cbtn_var.get() == 1:
                            #print "Enter hex recv\n"
                            self.receive_data = self.space_b2a_hex(self.receive_data)
                            #print "recv: ", self.receive_data
                            #如果接收到数据且发送不在测试模式下，上报采数数据
                            #print "receive data[0:2] :",self.receive_data[0:2], "\n"
                            #print "receive data[3:5] :",self.receive_data[3:5], "\n"
                            if (self.receive_data[0:2] == "07") and (self.test_mode_cbtn_var.get() == 0):
                                #print "receive data[0:2] :",self.receive_data[0:2], "\n"
                                if self.receive_data[3:5] == "03":
                                    #print "receive data[3:5] :",self.receive_data[3:5], "\n"
                                    self.send_data += "07"
                                    self.send_data_crc += "07"
                                    self.send_data += "03"
                                    self.send_data_crc += "03"
                                    #判断当前接收到的字节数
                                    byte_num = self.receive_data[15:17]
                                    print "byte_num = ",byte_num
                                    hex_byte_num = int(byte_num, 16)
                                    hex_response_byte_num = hex_byte_num * 2
                                    if hex_byte_num < 7:
                                        self.send_data += "0"
                                        self.send_data_crc += "0"
                                    str_response_byte_num = str(hex(hex_response_byte_num)).replace("0x", "")
                                    print "str_response_byte_num = ",str_response_byte_num
                                    self.send_data += str_response_byte_num
                                    self.send_data_crc += str_response_byte_num
                                    
                                    #对inNum进行处理
                                    #这个地方存在问题，当进出的人数大于255后会发生溢出，后续需要优化
                                    hexIn = hex(self.counter.inNum)
                                    if int(hexIn,16) < 16:
                                        self.send_data += str(hexIn).replace("x", "")
                                        self.send_data_crc += "00"
                                        self.send_data_crc += str(hexIn).replace("x", "")
                                    else:
                                        self.send_data += str(hexIn).replace("0x", "")
                                        self.send_data_crc += "00"
                                        self.send_data_crc += str(hexIn).replace("0x", "")

                                    #对outNum进行处理，方法与inNum一致
                                    hexOut = hex(self.counter.outNum)
                                    if int(hexOut,16) < 16:
                                        self.send_data += str(hexOut).replace("x", "")
                                        self.send_data_crc += "00"
                                        self.send_data_crc += str(hexOut).replace("x", "")
                                    else:
                                        self.send_data += str(hexOut).replace("0x", "")
                                        self.send_data_crc += "00"
                                        self.send_data_crc += str(hexOut).replace("0x", "")
                                    #对totleNum进行处理，方法与inNum一致
                                    if self.counter.totleNum < 0:
                                        self.send_data += "00"
                                        self.send_data_crc += "0000"
                                    else:
                                        hexTotle = hex(self.counter.totleNum)
                                        if int(hexTotle,16) < 16:
                                            self.send_data += str(hexTotle).replace("x", "")
                                            self.send_data_crc += "00"
                                            self.send_data_crc += str(hexTotle).replace("x", "")
                                        else:
                                            self.send_data += str(hexTotle).replace("0x", "")
                                            self.send_data_crc += "00"
                                            self.send_data_crc += str(hexTotle).replace("0x", "")
                                    
                                    loop = 0

                                    for loop0 in range(0,hex_byte_num - 3):
                                        self.send_data += "00"
                                    for loop1 in range(0, hex_response_byte_num - 6):
                                        self.send_data_crc += "00"

                                    print "Origin send_data = ", self.send_data
                                    print "Origin send_data_crc = ", self.send_data_crc
                                    
                                    #self.send_data = binascii.hexlify(self.send_data)
                                else:
                                    #print "receive data[3:5] error:",self.receive_data[3:5], "\n"
                                    self.send_data += "07"
                                    self.send_data += "83"
                                    self.send_data_crc += "07"
                                    self.send_data_crc += "83"
                            else:
                                print "receive data[0:2] error:",self.receive_data[1], "\n"
                                self.send_data += "07"
                                self.send_data += "83"
                                self.send_data_crc += "07"
                                self.send_data_crc += "83"
                            
                            self.crc = Crc16.crc16()
                            crc_high, crc_low = self.crc.createarray_string2hex(self.send_data_crc)
                            self.send_data_crc += crc_high
                            self.send_data_crc += crc_low
                        else:
                            print "Enter dec recv\n"
                            if self.receive_data.endswith("\n"):
                                print "Enter dec endswith\n"
                                self.receive_data = self.receive_data.strip()
                        print "insert recieve data"
                        self.frm_right_receive.insert("end", "[" + str(datetime.datetime.now()) + " - "
                                                      + str(self.receive_count) + "]:\n", "green")
                        self.frm_right_receive.insert("end", self.receive_data + "\n")
                        self.frm_right_receive.see("end")
                        self.receive_data = ""
                        time.sleep(0.01)
                        # 是否十六进制发送
                        if self.send_hex_cbtn_var.get() == 1:
                            #print "Enter hex send"
                            #self.send_data = self.space_b2a_hex(self.send_data)
                            self.ser.write(self.send_data_crc, isHex=True)
                        else:
                            self.ser.write(self.send_data_crc)
                        self.send_data = ""
                        self.send_data_crc = ""

            except Exception as e:
                logging.error(e)
                self.receive_data = ""
                self.ser.stop()
                self.ser = None

    def find_usb_tty(self, vendor_id=None, product_id=None):
        '''
        发现串口设备
        '''
        tty_devs = list()
        for dn in glob.glob('/sys/bus/usb/devices/*') :
            try:
                vid = int(open(os.path.join(dn, "idVendor" )).read().strip(), 16)
                pid = int(open(os.path.join(dn, "idProduct")).read().strip(), 16)
                if  ((vendor_id is None) or (vid == vendor_id)) and ((product_id is None) or (pid == product_id)) :
                    dns = glob.glob(os.path.join(dn, os.path.basename(dn) + "*"))
                    for sdn in dns :
                        for fn in glob.glob(os.path.join(sdn, "*")) :
                            if  re.search(r"\/ttyUSB[0-9]+$", fn) :
                                tty_devs.append(os.path.join("/dev", os.path.basename(fn)))
            except Exception as ex:
                pass
        return tty_devs

    def space_b2a_hex(self, data):
        '''
        格式化接收到的数据字符串
        示例：123 --> 31 32 33
        '''
        new_data_list = list()
        new_data = ""

        hex_data = binascii.b2a_hex(data)
        temp_data = ""
        for index,value in enumerate(hex_data): 
            temp_data += value
            if len(temp_data) == 2:
                new_data_list.append(temp_data)
                temp_data = ""
        for index,value in enumerate(new_data_list):
            if index%25 == 0 and index != 0:
                new_data += "\n"
            new_data += value
            new_data += " "

        return new_data

if __name__ == '__main__':
    '''
    main loop
    '''
    root = tk.Tk()
    root.title("SRT Contral")
    if SerialTool.g_default_theme == "dark":
        root.configure(bg="#292929")
        combostyle = ttk.Style()
        combostyle.theme_use('alt')
        combostyle.configure("TCombobox", selectbackground="#292929", fieldbackground="#292929",
                                          background="#292929", foreground="#FFFFFF")
    MainSerialToolUI(master=root)
    root.resizable(False, False)
    root.mainloop()