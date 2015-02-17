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
        Constructor.  Creates a new socket
        and does other initialization.
        '''
        self.port = port
        self.host = host
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        self.sequence = '0'

    def getMessages(self):
        '''
        Gets messages from the message board server.
        
        The first entry in the tuple is the return value,
        and has the following meaning:
        2 - no data received from server/nothing wrong happened
        1 - moar messages!
        0 - no messages
        -1 - something went wrong
        '''
        getMsg = "AGET"
        self.sock.sendto(getMsg.encode('utf8'), (self.host, self.port))

        readlist, writelist, errlist = select([self.sock], [], [], 0.1)
        if len(readlist) != 0:
            (msgs, serveraddr) = self.sock.recvfrom(1400)
        
            if msgs[0:3].decode() == "AOK" and len(msgs) > 4:
                msgs = msgs[4:].decode()
                return_msgs = msgs.split("::")
                return (1, return_msgs)
                #splitMsgs = 

            elif len(msgs.decode()) == 4:    # just "AOK "
                return (0, ["There are no messages on the server at this moment."])

            elif msgs[:6].decode() == "AERROR":   # something went horribly wrong!
                return (-1, msgs[7:].decode())
            else:
                return (2, 0)
        else:   # need to do something when no data
            return (2, 0)


    def postMessage(self, user, message):
        '''
        Posts a message to the message board server.
        
        The first entry in the tuple is the return value,
        and has the following meaning:
        2 - no data received from server/nothig
        0 - posting was fine
        -1 - something went wrong
        '''

        postMsg = "APOST " + user + "::" + message
        self.sock.sendto(postMsg.encode('utf8'), (self.host, self.port))
        readlist, writelist, errlist = select([self.sock], [], [], 0.1)
        if len(readlist) != 0:
            (msgs, serveraddr) = self.sock.recvfrom(1400)
            if msgs.decode() == "AOK":
                return (0, 0)
            elif msgs[:6].decode() == "AERROR":
                return (-1, msgs[7:].decode())   # after "AERROR "
            else:
                return (2, 0)
        else:   # no data? probably impossible but just to make sure
            return (2, 0)
            
    def gen_chksum(msg):
         
    def verify_chksum(chksum1, chksum2):
        return (chksum1 & chksum2) == chksum1
        


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

    def run(self):
        self.view.after(self.waittime, self.retrieve_messages)
        self.view.mainloop()
        
    def post_message_callback(self, m):
        (rv, error_m) = self.net.postMessage(myname, m)
        
        if rv == -1:
        	# just change the status
        	self.view.setStatus("Error when posting \"{}\", {}".format(m, error_m))
        elif rv == 0:   # everything went fine
            self.view.setStatus("Post success")
        else:   # no data received? do nothing
            pass

    def retrieve_messages(self):
        '''
        This method gets called every second for retrieving
        messages from the server.  It calls the MessageBoardNetwork
        method getMessages() to do the "hard" work of retrieving
        the messages from the server, then it should call 
        methods in MessageBoardView to display them in the GUI.
        '''
        
        # can increase refresh speed by decreasing that number
        # apparently in milliseconds
        self.view.after(self.waittime, self.retrieve_messages)
        (rv, msgs) = self.net.getMessages()
        
        if rv == -1:
            # just change the status
            error_msg = "Error when retrieving messages, {}".format(msgs)
            self.view.setStatus(error_msg)
        elif rv == 1:   # there are msgs on server
        
            mlist = []      # list of messages
            part_of_msg = 0 # either 0, 1, or 2 to indicate which part
            curr_msg = ""   # current message to assemble
            
            for msg_part in msgs:
                curr_msg += msg_part + " "
                if part_of_msg == 2:    # after added everything for 1 message
                    mlist += [curr_msg] # append current message to list
                    curr_msg = ""       # clear current message
                part_of_msg = (part_of_msg + 1) % 3 # every message has 3 parts
            
            self.view.setListItems(mlist)
        elif rv == 0:   # no messages on server
            self.view.setStatus([msgs])
        elif rv == 2:   # no data? pass
            pass
                

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

