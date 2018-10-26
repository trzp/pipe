#!usr/bin/python
# -*- coding: utf-8 -*-
# Author: mr tang
# Date:   2018-10-26 22:25:45
# Contact: mrtang@nudt.edu.cn
# Github: trzp
# Last Modified by:   mr tang
# Last Modified time: 2018-10-27 00:47:29

# named pipe Server
# encoding: utf-8


import win32file
import win32pipe
import time
import threading


'''
usage:
    WinNamedPipeServer: init -> accept (block) -> write
    WinNamedPipeClient: init -> connect (use after server established, or an exception throw) -> read

    asyWinNamedPipeServer: init -> put (call at any time, if clinet is not connected, the data will be discarded
                                    use self.ok to check the state)
    asyWinNamedPipeClient: init -> get (call at any time, if server is not establised, no data recved,)
'''

class WinNamedPipeServer:
    def __init__(self, pipe_name):
        self.pipe = win32pipe.CreateNamedPipe(r'\\.\pipe\%s' % pipe_name,  # 固定的命名方式
                                              win32pipe.PIPE_ACCESS_DUPLEX,
                                              win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                                              1, 65536, 65536,
                                              0,
                                              None)

    def accept(self):
        '''block until a client connected'''
        win32pipe.ConnectNamedPipe(self.pipe, None)

    def close(self):
        win32file.CloseHandle(self.pipe)

    def write(self, buf):
        win32file.WriteFile(self.pipe, buf)


class WinNamedPipeClient:
    def __init__(self, pipe_name):
        self.pipe_name = pipe_name

    def connect(self):
        '''connect to server pipe'''
        self.handle = win32file.CreateFile(r'\\.\pipe\%s' % self.pipe_name,
                                           win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                                           0,
                                           None,
                                           win32file.OPEN_EXISTING,
                                           0,
                                           None
                                           )
        win32pipe.SetNamedPipeHandleState(
            self.handle, win32pipe.PIPE_READMODE_MESSAGE, None, None)

    def read(self):
        return win32file.ReadFile(self.handle, 64*1024)[1]

class asyWinNamedPipeServer(threading.Thread):
    def __init__(self,pipe_name):
        self.ok = False
        self.__pipe = WinNamedPipeServer(pipe_name)
        super(asyWinNamedPipeServer,self).__init__()
        self.setDaemon(True)
        self.start()

    def run(self):
        self.__pipe.accept()
        self.ok = True

    def put(self,buf):
        if self.ok:
            self.__pipe.write(buf)
        return self.ok

    def close(self):
        self.__pipe.close()

class asyWinNamedPipeClient(threading.Thread):
    def __init__(self,pipe_name,time_out=30): #timeout: seconds
        self.ok = False
        self.__to = time_out
        self.__pipe = WinNamedPipeClient(pipe_name)
        super(asyWinNamedPipeClient,self).__init__()
        self.setDaemon(True)
        self.start()

    def run(self):
        clk = time.clock()+self.__to
        while time.clock()<clk:
            try:
                self.__pipe.connect()
                self.ok = True
                break
            except:
                pass

            time.sleep(0.1)

    def get(self):
        if self.ok:
            return 1,self.__pipe.read()
        else:
            return 0,0

