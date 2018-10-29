#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: mr tang
# Date:   2018-10-29 15:50:37
# Contact: mrtang@nudt.edu.cn
# Github: trzp
# Last Modified by:   mr tang
# Last Modified time: 2018-10-29 16:48:22

import os
from struct import unpack
from threading import Event
import threading
import socket
import time
import re
import getpass

username = getpass.getuser()

class UnixNamedPipeServer():
    def __init__(self, pipe_name):
        abspath = '/home/%s/tem/'%username
        self.pipe_name_w = abspath+pipe_name+'ww.out'
        if not os.path.exists(self.pipe_name_w):
            os.mkfifo(self.pipe_name_w)

    def init(self): #keep accordance with WinNamedPipe
        self.wf = os.open(self.pipe_name_w, os.O_SYNC | os.O_CREAT | os.O_RDWR)

    def put(self, buf):
        os.write(self.wf, buf)

    def close(self):
        os.close(self.wf)

class hUnixNamedPipeServer(threading.Thread):
    '''
    This class is used a couple with hUnixNamedPipeClient. 
    You can call the 'put' method at any time, but the data 
    will only be really sent when there is a client request, 
    otherwise, the data will be discarded. This class 
    keeps checking (per 0.5s) whether a client is 
    requesting data. You can check self.ok to confirm 
    the client request status.
    '''
    def __init__(self,pipe_name,ID):
        threading.Thread.__init__(self)
        self.pipe = UnixNamedPipeServer(pipe_name)
        self.pipe.init()
        self.ok = False
        self.setDaemon(True)
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.sock.settimeout(1) #延迟1秒 客户端每0.5秒发送一次请求
        self.sock.bind(('127.0.0.1',ID))
        self.__ev = Event()
        self.start()

    def run(self):  #心跳检测，能够在任何被请求的时候做出响应
        while True:
            if self.__ev.isSet():break
            try:
                self.sock.recvfrom(128)     #每次最多等待1秒
                self.ok = True  #能够正常受到客户端的请求
            except:
                self.ok = False

    def put(self,buf,head='__LIVE__'):
        if self.ok:   self.pipe.put(head+buf)
        return self.ok

    def close(self):
        self.__ev.set()
        self.put('','__DEAD__')
        self.pipe.close()

        
class UnixNamedPipeClient:
    def __init__(self, pipe_name):
        abspath = '/home/%s/tem/'%username
        self.pipe_name_r = abspath+pipe_name+'ww.out'

        if not os.path.exists(self.pipe_name_r):
            os.mkfifo(self.pipe_name_r)

        self.rf = os.open(self.pipe_name_r, os.O_RDONLY)

    def get(self,bufsize):
        return os.read(self.rf,bufsize)

    def close(self):
        os.close(self.rf)
        
class hUnixNamedPipeClient(threading.Thread):
    '''
    This class is used a couple with hUnixNamedPipeServer. 
    You can call the 'get' method to get data from server,
    if the server is alive, the get method will block until
    the data recieved, once the server is killed, the get
    method will became nonblocking. We provided self.ok variable
    to check whether the server is alive.

    set self.acquire = True to acquire data from server. 
    be aware that after self.acquire is set, you should immediately
    call get method, or you would get more than one data
    
    '''
    def __init__(self, pipe_name,ID):
        self.pipe = UnixNamedPipeClient(pipe_name)
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.addr = ('127.0.0.1',ID)
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.start()
        self.ok = True
        self.acquire = False
        self.__ev = Event()

    def run(self):  #发送心跳包
        while True:
            if self.__ev.isSet():break
            if self.acquire: self.sock.sendto('ok',self.addr)
            time.sleep(0.5)
    
    def get(self,bufsize):
        buf = self.pipe.get(bufsize)
        head = buf[:8]
        content = buf[8:]
        if head == '__LIVE__':
            self.ok = True
            return content
        else:
            self.ok = False
            return ''

    def close(self):
        self.__ev.set()
        self.pipe.close()
