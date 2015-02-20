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
import time

class MessageBoardNetwork(object):
	'''
	Model class in the MVC pattern.  This class handles
	the low-level network interactions with the server.
	It should make GET requests and POST requests (via the
	respective methods, below) and return the message or
	response data back to the MessageBoardController class.
	'''
	def __init__(self, host, port, retries, timeout):
		'''
		Constructor.  Creates a new socket
		and does other initializations.
		'''
		# public fields
		self.port = port
		self.host = host
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
		
		# configurable parameters
		self.timeout = timeout
		self.retries = retries

		# private fields
		self._curr_seqn = 0
		self._max_msg_size = 1400

	# private helper methods

	def _gen_chksum(self, encoded_msg):
		'''
		bytes -> int
		'''
		chksum = encoded_msg[0] ^ encoded_msg[1]
		for i in range(2, len(encoded_msg)):
			chksum ^= encoded_msg[i]
		return chksum
		 
	def _chksum_correct(self, chksum1, chksum2):
		'''
		(int, int) -> bool
		'''
		return (chksum1 & chksum2) == chksum1

	def _update_seqn(self):
		if self._curr_seqn == 0:
			self._curr_seqn = 1
		else:
			self._curr_seqn = 0

	# public methods

	def getMessages(self):
		'''
		Gets messages from the message board server.
		
		The first entry in the tuple is the return value,
		and has the following meaning:
		2 - no data received from server/nothing wrong happened
		1 - moar messages!
		0 - no messages
		-1 - something went wrong (server side msg)
		-2 - request failed (too many retries)
		'''

		# deal with sending message
		encoded_get = "GET".encode()
		chksum = self._gen_chksum(encoded_get)	# generate checksum
		get_msg = ("C" + str(self._curr_seqn)).encode() + bytes([chksum]) + encoded_get
		self.sock.sendto(get_msg, (self.host, self.port))

		# deal with message received
		readlist, writelist, errlist = select([self.sock], [], [], self.timeout)
		num_retries = 0

		# timed out! wait
		while len(readlist) == 0:
			num_retries += 1
			if num_retries > self.retries:
				return (-2, 0)	# too many retries, fail

			# try again
			self.sock.sendto(get_msg, (self.host, self.port))

			# wait
			readlist, writelist, errlist = select([self.sock], [], [], self.timeout)

		# success! receive
		(msgs, serveraddr) = self.sock.recvfrom(self._max_msg_size)
		
		# check header info
		actual_chksum = self._gen_chksum(msgs[3:])
		recvd_chksum = msgs[2]
		version = chr(msgs[0])
		seqn = int(chr(msgs[1]))

		# header incorrect! retry
		while not (self._chksum_correct(recvd_chksum, actual_chksum) and 	# checksum needs to be right
				   version == 'C' and 										# version needs to be right
				   self._curr_seqn == seqn):								# seq. no. needs to be right 
			# try again
			self.sock.sendto(get_msg, (self.host, self.port))

			readlist, writelist, errlist = select([self.sock], [], [], self.timeout)

			# timed out! wait
			while len(readlist) == 0:
				num_retries += 1
				if num_retries > self.retries:
					return (-2, 0)	# too many retries, fail

				# try again
				self.sock.sendto(get_msg, (self.host, self.port))

				# wait
				readlist, writelist, errlist = select([self.sock], [], [], self.timeout)

			# get the message
			(msgs, serveraddr) = self.sock.recvfrom(self._max_msg_size)

			# check header again
			actual_chksum = self._gen_chksum(msgs[3:])
			recvd_chksum = msgs[2]
			version = chr(msgs[0])
			seqn = int(chr(msgs[1]))

		# everything correct: now check app layer content
		if msgs[3:5].decode() == "OK" and len(msgs) > 5:	# after header and "OK"
			msgs = msgs[5:].decode()						# which is 5 characters
			return_msgs = msgs.split("::")
			self._update_seqn()
			return (1, return_msgs)
		elif len(msgs) == 5:    # just "OK", no messages
			self._update_seqn()
			return (0, ["no messages currently"])
		elif msgs[3:8].decode() == "ERROR":		# after header and "ERROR"
			self._update_seqn()
			return (-1, msgs[8:].decode())		# which is 8 characters
		else:	# something else happened?
			self._update_seqn()
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

		postmsg = ("POST " + user + "::" + message).encode()
		chksum = self._gen_chksum(postmsg)
		complete_post = ("C" + str(self._curr_seqn)).encode() + bytes([chksum]) + postmsg
		self.sock.sendto(complete_post, (self.host, self.port))

		readlist, writelist, errlist = select([self.sock], [], [], self.timeout)
		num_retries = 0

		# timed out! wait
		while len(readlist) == 0:
			num_retries += 1
			if num_retries > self.retries:
				return (-2, 0)	# too many retries, fail

			# try again
			self.sock.sendto(complete_post, (self.host, self.port))

			# wait
			readlist, writelist, errlist = select([self.sock], [], [], self.timeout)

		# success! receive
		(msgs, serveraddr) = self.sock.recvfrom(self._max_msg_size)
		
		# check header info
		actual_chksum = self._gen_chksum(msgs[3:])
		recvd_chksum = msgs[2]
		version = chr(msgs[0])
		seqn = int(chr(msgs[1]))

		# header incorrect! retry
		while not (self._chksum_correct(recvd_chksum, actual_chksum) and 	# checksum needs to be right
				   version == 'C' and 										# version needs to be right
				   self._curr_seqn == seqn):								# seq. no. needs to be right 
			# try again
			self.sock.sendto(complete_post, (self.host, self.port))

			readlist, writelist, errlist = select([self.sock], [], [], self.timeout)

			# timed out! wait
			while len(readlist) == 0:
				num_retries += 1
				if num_retries > self.retries:
					return (-2, 0)	# too many retries, fail

				# try again
				self.sock.sendto(complete_post, (self.host, self.port))

				# wait
				readlist, writelist, errlist = select([self.sock], [], [], self.timeout)

			# get the message
			(msgs, serveraddr) = self.sock.recvfrom(self._max_msg_size)

			# check header again
			actual_chksum = self._gen_chksum(msgs[3:])
			recvd_chksum = msgs[2]
			version = chr(msgs[0])
			seqn = int(chr(msgs[1]))

		if msgs[3:5].decode() == "OK":
			self._update_seqn()
			return (0, 0)
		elif msgs[3:8].decode() == "ERROR":
			self._update_seqn()
			return (-1, msgs[8:].decode())   # after "ERROR"
		else:
			self._update_seqn()
			return (2, 0)
		


class MessageBoardController(object):
	'''
	Controller class in MVC pattern that coordinates
	actions in the GUI with sending/retrieving information
	to/from the server via the MessageBoardNetwork class.
	'''

	def __init__(self, myname, host, port, retries, timeout, waittime):
		self.name = myname
		self.view = MessageBoardView(myname)
		self.view.setMessageCallback(self.post_message_callback)
		self.net = MessageBoardNetwork(host, port, retries, timeout)
		self.waittime = waittime

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
		
		if rv == -1:	# something went wrong on server side
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
		elif rv == -2:	# failed due to too many retries
			error_msg = "Post message failed: too many retries"
			self.view.setStatus(error_msg)

				

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
	parser.add_argument("--retries", dest='retries', type=int, default=10,
						help='Set the number of retransmissions in case of a timeout (default: 3)')
	parser.add_argument("--timeout", dest='timeout', type=float, default=0.1,
						help='Set the RTO value (default: 0.1)')
	parser.add_argument("--refreshrate", dest='waittime', type=int, default=1000,
						help='Set the refresh rate of the chat screen (default: 1000)')

	args = parser.parse_args()

	myname = input("What is your user name (max 8 characters)? ")

	app = MessageBoardController(myname, args.host, args.port, args.retries, args.timeout, args.waittime)
	app.run()

