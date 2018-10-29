#!usr/bin/python
# -*- coding: utf-8 -*-
# Author: mr tang
# Date:   2018-10-26 22:25:45
# Contact: mrtang@nudt.edu.cn
# Github: trzp
# Last Modified by:   mr tang
# Last Modified time: 2018-10-29 16:36:06

# named pipe Server
# encoding: utf-8


import win32file
import win32pipe
import time
import threading
import pywintypes
import thread


'''
usage:
    WinNamedPipeServer: instantiation -> accept (block) -> write
    WinNamedPipeClient: instantiation -> connect (use after server established, or an exception throw) -> read

    hWinNamedPipeServer: instantiation -> put (call at any time, if clinet is not connected, the data will be discarded
                                    if the connect is broken, the connection will be rebuild automatically, use self.ok 
                                    to check the state)
    hWinNamedPipeClient: instantiation -> get (call at any time, if server is not establised, no data recved,
                                    this class is not suggest to use)
'''

class WinNamedPipeServer:
    def __init__(self, pipe_name):
        self.pipe_name = pipe_name

    def init(self):
        self.pipe = win32pipe.CreateNamedPipe(r'\\.\pipe\%s' % self.pipe_name,  # 固定的命名方式
                                              win32pipe.PIPE_ACCESS_DUPLEX,
                                              win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                                              1, 65536, 65536,
                                              0,
                                              None)

    def accept(self):
        '''block until a client connected'''
        win32pipe.ConnectNamedPipe(self.pipe, None)

    def close(self):
        try:
            win32pipe.DisconnectNamedPipe(self.pipe)
            win32file.CloseHandle(self.pipe)
            return 1
        except:
            return 0

    def put(self, buf):
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

    def get(self):
        return win32file.ReadFile(self.handle, 64*1024)[1]

class hWinNamedPipeServer:
    '''
    unblock connecting to client, and can rebuild connection automatically
    '''
    def __init__(self,pipe_name):
        self.__pipe = WinNamedPipeServer(pipe_name)
        self.ok = False
        self.__taccept()

    def __accept(self):
        self.__pipe.close()
        self.__pipe.init()
        self.__pipe.accept()
        self.ok = True

    def __taccept(self):    #connect to client in sub-thread so that main thread would not be block
        thread.start_new_thread(self.__accept,())

    def put(self,buf):
        ''' connection rebuild automatically
            return value: 1-succeed 0-failure
        '''
        if self.ok:
            try:
                self.__pipe.put(buf)
                return 1
            except:
                self.ok = False
                self.__taccept()
                return 0
        else:
            return 0

    def close(self):
        self.__pipe.close()


class hWinNamedPipeClient:
    '''
    automatically connect to server when server is closed
    '''
    def __init__(self, pipe_name):
        self.ok = False
        self.__pipe = hWinNamedPipeClient(pipe_name)
        self.__tconnect()

    def __connect(self):
        while True:
            try:
                self.__pipe.connect()
                self.ok = True
                break
            except:
                pass
            time.sleep(0.2)

    def __tconnect(self):
        thread.start_new_thread(self.__connect,())

    def get(self):
        if self.ok:
            try:
                buf = win32file.ReadFile(self.handle, 64*1024)[1]
                return [1,buf]
            except:
                self.ok = False
                self.__tconnect()
                return [0,'']
        else:
            return [0,'']

