#!/usr/bin/env python3

__author__ = "jsommers@colgate.edu, mliu@colgate.edu, dhuang@colgate.edu"
__doc__ = '''
A simple model-view controller-based message board/chat client application.
'''
import sys
if sys.version_info[0] != 3:
    print ("This code must be run with a python3 interpreter!")
    sys.exit()

import tkinter
import socket
from select import select
import argparse

class MessageBoardNetwork(object):
    '''
    Model class in the MVC pattern.  This class handles
    the low-level network interactions with the server.
    It should make GET requests and POST requests (via the
    respective methods, below) and return the message or
    response data back to the MessageBoardController class.
    '''
    def __init__(self, host, port):
        '''
        Constructor.  You should create a new socket
        here and do any other initialization.
        '''
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        self.host = host
        self.sock.bind((host, port))

    def getMessages(self):
        '''
        You should make calls to get messages from the message 
        board server here.
        '''
        getMsg = "AGET"
        self.sock.sendto(getMsg.encode('utf8'), (self.server, self.port))

        readlist, writelist, errlist = select.select(self.sock, [], [], 0.1)
        if len(readlist) != 0;
            (Msgs, serveraddr) = self.sock.recvfrom(1400)
        
            if Msgs[0:2].decode() == "OK" and len(Msgs) > 4:
                Msgs = Msgs[4:]
                splitMsgs = 

            elif len(Msgs) == 3:
                return ["There is no message at the server at this moment."]

            else:
                return ["Error", Msgs[7:]]


    def postMessage(self, user, message):
        '''
        You should make calls to post messages to the message 
        board server here.
        '''

        postMsg = "APOST " + user + "::" + message
        self.sock.sendto(postMsg.encode('utf8'), (self))
        (Msgs, serveraddr) = self.sock.recvfrom()
        if Msgs[0:2].decode() == "OK" and len(Msgs) == 2:
            return (0,0)
        else:
            return (-1, Msgs[7:])


class MessageBoardController(object):
    '''
    Controller class in MVC pattern that coordinates
    actions in the GUI with sending/retrieving information
    to/from the server via the MessageBoardNetwork class.
    '''

    def __init__(self, myname, host, port):
        self.name = myname
        self.view = MessageBoardView(myname)
        self.view.setMessageCallback(self.post_message_callback)
        self.net = MessageBoardNetwork(host, port)
        self.waittime = 300	# refresh every 0.3s
        self.prev_msgs = []	# create empty list to store messages

    def run(self):
        self.view.after(waittime, self.retrieve_messages)
        self.view.mainloop()
        
    def post_message_callback(self, m):
        rv = self.net.postMessage(myname, m)
        
        if rv[:5] == "AERROR":
        	# just change the status
        	self.view.setStatus("Error when posting " + m)
        elif rv[:2] == "AOK":
        	# posting was a-ok
        	# view cannot add one line at a time
        	# how to get previous messages?
        	# create instance variable in controller class?
        	# --> let retrieve_messages handle it since that
        	#     is periodically called
        	# so just ignore?
        	
        
        

    def retrieve_messages(self):
        '''
        This method gets called every second for retrieving
        messages from the server.  It calls the MessageBoardNetwork
        method getMessages() to do the "hard" work of retrieving
        the messages from the server, then it should call 
        methods in MessageBoardView to display them in the GUI.

        You'll need to parse the response data from the server
        and figure out what should be displayed.

        Two relevant methods are (1) self.view.setListItems, which
        takes a list of strings as input, and displays that 
        list of strings in the GUI, and (2) self.view.setStatus,
        which can be used to display any useful status information
        at the bottom of the GUI.
        '''
        
        # can increase refresh speed by decreasing that number
        # apparently in milliseconds
        self.view.after(waittime, self.retrieve_messages)
        self.prev_msgs = self.net.getMessages()


class MessageBoardView(tkinter.Frame):
    '''
    The main graphical frame that wraps up the chat app view.
    This class is completely written for you --- you do not
    need to modify the below code.
    '''
    def __init__(self, name):
        self.root = tkinter.Tk()
        tkinter.Frame.__init__(self, self.root)
        self.root.title('{} @ messenger465'.format(name))
        self.width = 80
        self.max_messages = 20
        self._createWidgets()
        self.pack()

    def _createWidgets(self):
        self.message_list = tkinter.Listbox(self, width=self.width, height=self.max_messages)
        self.message_list.pack(anchor="n")

        self.entrystatus = tkinter.Frame(self, width=self.width, height=2)
        self.entrystatus.pack(anchor="s")

        self.entry = tkinter.Entry(self.entrystatus, width=self.width)
        self.entry.grid(row=0, column=1)
        self.entry.bind('<KeyPress-Return>', self.newMessage)

        self.status = tkinter.Label(self.entrystatus, width=self.width, text="starting up")
        self.status.grid(row=1, column=1)

        self.quit = tkinter.Button(self.entrystatus, text="Quit", command=self.quit)
        self.quit.grid(row=1, column=0)


    def setMessageCallback(self, messagefn):
        '''
        Set up the callback function when a message is generated 
        from the GUI.
        '''
        self.message_callback = messagefn

    def setListItems(self, mlist):
        '''
        mlist is a list of messages (strings) to display in the
        window.  This method simply replaces the list currently
        drawn, with the given list.
        '''
        self.message_list.delete(0, self.message_list.size())
        self.message_list.insert(0, *mlist)
        
    def newMessage(self, evt):
        '''Called when user hits entry in message window.  Send message
        to controller, and clear out the entry'''
        message = self.entry.get()  
        if len(message):
            self.message_callback(message)
        self.entry.delete(0, len(self.entry.get()))

    def setStatus(self, message):
        '''Set the status message in the window'''
        self.status['text'] = message

    def end(self):
        '''Callback when window is being destroyed'''
        self.root.mainloop()
        try:
            self.root.destroy()
        except:
            pass

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='COSC465 Message Board Client')
    parser.add_argument('--host', dest='host', type=str, default='localhost',
                        help='Set the host name for server to send requests to (default: localhost)')
    parser.add_argument('--port', dest='port', type=int, default=1111,
                        help='Set the port number for the server (default: 1111)')
    args = parser.parse_args()

    myname = input("What is your user name (max 8 characters)? ")

    app = MessageBoardController(myname, args.host, args.port)
    app.run()

