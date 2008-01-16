# -*- Mode: Python; tab-width: 4; py-indent-offset: 4; -*-
#
# Simple python client/server system to provide remote access
# to TDT COM interface from a linux box (or anyother system
# running python) over the network.
#
# NOTE -- this implments a *simple* server -- only one client
#         at a time!
#
############################################################################
# SERVER SIDE
############################################################################
#
# This module, WHEN RUN AS A PROGRAM ON A WINDOWS MACHINE, implments
# the server. At startup, the program tries to connect to TDevAcc
# (direct access to workbench) and a TTank (data tank) COM
# services. Then it just listens for incomming connections
# on port 10000 (from pype or anything else on the the
# network).
#
# The client then sends commands as pickled strings. For each
# picked string the client sends, the server will eval() the
# string and return a pickled tuple of length 2. Either:
#   (1, result-object)
#   (None, None)
# The first value indicates whether an error occured during
# execution. If it's 1, then execution was a sucess and the
# result is returned.
#
############################################################################
# CLIENT SIDE
############################################################################
#
#
#
############################################################################
# Socket Classes derrived from:
#    Socket utilities class by Amey R Pathak
#    src: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/200946
############################################################################

import sys
import time
import socket
import pickle

try:
	from Numeric import *
except ImportError:
	pass


# OpenEx run modes
IDLE = 0								# dsp completely idle
STANDBY = 1								# running, no display, no tank..
PREVIEW = 2								# running, not saving to tank
RECORD = 3								# running and saving all data

def Hostname():
	return socket.gethostname()

class _SocketServer:
	def __init__(self, host = Hostname(), port = 10000):
		self.host, self.port = host, port
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.bind((self.host, self.port))
		self.remoteHost = None
		
	def Listen(self):
		self.sock.listen(1)
		self.conn, self.remoteHost = self.sock.accept()
		self.remoteHost = self.remoteHost[0]
			
	def Send(self, data):
		return self.conn.send(data)

	def Receive(self, size = 1024):
		return self.conn.recv(size)
	
	def Close(self):
		self.sock.close()
		
	def __str__(self):
		return '<_SocketServer '+\
			   str(self.host)+':'+str(self.port)+'>'

class _SocketClient:
	def __init__(self):
		self.host, self.port = None, None
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def Connect(self, remoteHost = Hostname(), remotePort = 10000):
		self.remoteHost, self.remotePort = remoteHost, remotePort
		# 1 second timeout		
		self.sock.settimeout(1)
		# generates exception on failure-to-connect
		self.sock.connect((self.remoteHost, self.remotePort))
		
	def Send(self, data):
		return self.sock.send(data)
		
	def Receive(self, size = 1024):
		return self.sock.recv(size)
	
	def Close(self):
		self.sock.close()
		
	def __str__(self):
		return '<_SocketClient '+\
			   str(self.remoteHost)+':'+str(self.remotePort)+'>'

class TDTServer:
	"""
	Wrapper object for the server. To setup a server, you simply
	do something like this:
	
	  s = Server()
	  s.listen()

	The server doesn't connect to the TDT subsystem until a client
	get's connected. If it can't make the connection, it reports
	an error by pushing a '0' instead of a '1' back to the client
	upon connection.

	This means you can leave the python server running all the time
	and it will connect to the TDT stuff at will...

	** This should be instantiated on a Windows system ONLY **
	"""
	def __init__(self, Server='Local', tk=None):
		# importing win32com stuff will fail on a unix box, so be
		# ready to print an error message and die..
		import win32com.client
		global TDevAcc, TTank

		self.Server = Server
		TDevAcc = win32com.client.Dispatch('TDevAcc.X')
		TTank = win32com.client.Dispatch('TTank.X')
		self.connected = None

	def connect(self):
		"""
		Set up connections to the TDT COM server
		"""
		global TDevAcc, TTank

		if self.connected:
			sys.stderr.write('already connected to TDT servers...\n')
			return 1
			
		sys.stderr.write('Connecting to TDT servers...\n')

		(devConn, tankConn) = (0, 0)

		for tries in range(10):
			try:
				if not devConn:
					devConn = TDevAcc.ConnectServer(self.Server)
			except:
				pass
			
			try:
				if not tankConn:
					tankConn = TTank.ConnectServer(self.Server, 'Me')
			except:
				pass

			if devConn and tankConn:
				sys.stderr.write('Connect to TDevAcc and TTank.<%s>.\n' %
								 self.Server)
				self.connected = 1
				return 1
			else:
				time.sleep(1)

		if not devConn:
			sys.stderr.write('No connect to %s.TDevAcc (%d tries)\n' %
						 (self.Server, tries))
		if not tankConn:
			sys.stderr.write('No connect to %s.TTank (%d tries)\n' %
						 (self.Server, tries))

		return 0

	def disconnect(self):
		TDevAcc.CloseConnection()
		TTank.CloseConnection()

	def listen(self):
		global TDevAcc, TTank

		while 1:
			server = _SocketServer()
			sys.stderr.write("Waiting for client..\n")
			server.Listen()
			sys.stderr.write("Received connection from %s\n" % \
							 server.remoteHost)

			if not self.connect():
				server.Send(pickle.dumps(0))
				sys.stderr.write("Abort.\n")
			else:
				server.Send(pickle.dumps(1))
				sys.stderr.write("Ready.\n")
				while 1:
					try:
						x = pickle.loads(server.Receive())
					except EOFError:
						# client closed connection
						break
					
					try:
						ok = 1
						result = eval(x)
					except:
						ok = None
						result = None
					server.Send(pickle.dumps((ok, result)))
					if 0:
						sys.stderr.write('(%s,"%s") <- %s\n' % (ok, result, x))
					else:
						sys.stderr.write('.');
						sys.stderr.flush();
					if ok is None:
						sys.stderr.write('%s\n' % sys.exc_value)
			sys.stderr.write("\nClient closed connection.\n")
			server.Close()
			#this fails:
			#self.disconnect()
	
class TDTClient:
	def __init__(self, server):
		self.server = server
		self.client = None
		
		self.open_conn()

		(self.nchans, self.sniplen) = self.chaninfo()
		(ok, self.fs) = self.send("TDevAcc.GetDeviceSF('Amp1')")

	def open_conn(self):
		"""
		Connect to the remote server sepcified during initialization
		and exchange sync information.

		The default timeout (set above) is 1s, so if this throws and
		exception or error, it's likely the server's not running on
		the TDT size.
		"""
		if self.client is None:
			self.client = _SocketClient()
			self.client.Connect(self.server)
		ok = pickle.loads(self.client.Receive())
		if not ok:
			raise EOFError
		
	def close_conn(self):
		"""
		Shut down connection.
		"""
		self.client.Close()
		self.client = None

	def send(self, cmd):
		"""
		Send a command string for remove evaluation to the server.
		Command string (cmd) should be a valid python expression
		that can be eval'ed in the remote envrionment. Access to
		the Tucker-Davis API is via:
		  TDevAcc (for the direct DSP interface), or,
		  TTank (for access to the data tank)

		The return value is a pair: (statusFlag, resultValue), where
		statusFlag is 1 for normal evaluation and 0 for an error and
		resultValue is the actual value returned by the function
		call (the value is pickled on the Server side and returns, so
		data typing should be correctly preserved and propagated.
		"""
		if self.client is None:
			self.open_conn()
		try:
			self.client.Send(pickle.dumps(cmd))
			(ok, result) = pickle.loads(self.client.Receive())
			if 0:
				# debugging
				print (ok, result), "<-", cmd
		finally:
			#self.close_conn()
			pass
		return (ok, result)

	def mode(self, mode=None, name=None):
		"""
		Query current run mode for the TDT device.

		Run modes are defined by TDT as follows (and also declared
		as global constants/vars in this file):
		  IDLE = 0		# dsp completely idle
		  STANDBY = 1	# running, no display, no tank..
		  PREVIEW = 2	# running, not saving to tank
		  RECORD = 3	# running and saving all data
		"""

		if not mode is None:
			(ok, r) = self.send('TDevAcc.SetSysMode(%d)' % mode)
			if ok is None:
				sys.stderr.write("tdt: can't set mode\n")
				return None			
		else:
			(ok, r) = self.send('TDevAcc.GetSysMode()')
			if ok is None:
				sys.stderr.write("tdt: can't get mode\n")
				return None
			if name:
				modes = { IDLE:'IDLE', STANDBY:'STANDBY',
						  PREVIEW:'PREVIEW', RECORD:'RECORD'}
				r = modes[r]
		return r

	def tank(self, tankpath=None, live=None):
		"""
		Get or Set pathname for DataTank. This is where data gets saved.
		If tankpath is specified, it's the filename on the window's machine.
		if live==1, then the tank server will automaticaly select the
		active tank that OpenEx is writing to.

		The live flag refers the the DataTank -- that is if you want to
		access data from the tank (lagging behind a bit). If live=1, then
		the selected READABLE DataTank will be pointed towards the
		currently being WRITTEN Datatank..

		Specify tankpath OR live, but not both!
		"""
		if tankpath:
			(ok, r) = self.send('TDevAcc.SetTankName("%s")' % tankpath)
		elif live:
			(ok, r) = self.send('TTank.OpenTank(TDevAcc.GetTankName(), "R")')
		else:
			(ok, r) = self.send('TDevAcc.GetTankName()')
		if ok is None:
			sys.stderr.write('TDT Error!\n')
			return None
		return r

	def tnum(self, reset=None):
		"""
		Read trial count, or if reset==1 reset the counter to zero. This
		should really be done when OpenEx is in standby mode..
		"""
		if reset:
			(ok, r) = self.send('TDevAcc.SetTargetVal("Amp1.TNumRst", 1)')
			(ok, r) = self.send('TDevAcc.SetTargetVal("Amp1.TNumRst", 0)')
		else:
			(ok, r) = self.send('TDevAcc.GetTargetVal("Amp1.TNum")')
		if ok is None:
			sys.stderr.write('TDT Error!\n')
			return None
		return int(r)

	def chaninfo(self):
		"""
		Figure out number of analog channels and length of spike snippet.
		The actual length of the snippet is hoopsize/3 points, since
		cSnip refers to the hoops, not the waveform.
		"""
		n = 1
		while 1:
			(ok, s) = self.send("TDevAcc.GetTargetSize('Amp1.cSnip~%d')" % n)
			if s == 0:
				break
			if n == 1:
				hoopsize = s
			n = n + 1
		return (n-1, hoopsize/3)

	def getblock(self):
		"""
		Query current block info -- this is enough info to find the current
		data record later (assuming tank doesn't get deleted...)
		"""
		(ok, block) = self.send('TTank.GetHotBlock()')
		return (self.server, self.tank(), block, self.tnum())
		

	def newblock(self, record=1):
		"""
		Start a new block in the current tank. Each block corresponds
		to a single run. If record==1, then a new block is started for
		recording. Otherwise, the current block is terminated and the
		system is left in standby mode.

		Basically, you should call newblock(record=1) at the start
		of a run and then neweblock(record=0) at the end.

		NOTE: In IDLE and STANDBY mode, GetHotBlock() returns an empty
		string, in PREVIEW mode 'TempBlock' and in RECORD mode a true
		block name (typically 'Block-NNN')

		RETURNS: (servername, tankname, blockname); this should be enough
		info to track down the location of the record no matter what..
		"""
		
		# make sure the live tank is selected
		self.tank(live=1)

		# set OpenEx to STANDBY and wait for this to register in the
		# tank as a change in the block name to '' (or if it was already
		# in STANDBY mode, we're good to go..
		self.mode(STANDBY)
		while 1:
			(ok, oldblock) = self.send('TTank.GetHotBlock()')
			if len(oldblock) == 0:
				break

		# reset the trial counter
		self.tnum(reset=1)

		# switch back to record mode and wait for this to get into the
		# tank, so we can store the block name for easy access later..
		if record:
			self.mode(RECORD)
			while 1:
				(ok, newblock) = self.send('TTank.GetHotBlock()')
				if not (newblock == oldblock):
					break
		else:
			newblock = oldblock
			
		# and return the tank & block name --> this is enough info to
		# find the record later..
		return (self.server, self.tank(), newblock)


	def count(self, d):
		actchans = 0
		actunits = 0
		for n in range(1, self.nchans+1):
			t = d[n, 'thresh']
			h = d[n, 'hoops']

			k = sum(not_equal(h[::3], 0.0))
			if k > 0:
				actchans = actchans + 1
			actunits = actunits + k
		print "%d active electrodes" % actchans
		print "%d active units" % actunits

	def sortparams(self, params=None):
		if params is None:
			params = {}
			for n in range(1, self.nchans+1):
				(ok, t) = \
					 self.send("TDevAcc.GetTargetVal('Amp1.aSnip~%d')" %
									(n, ))
				(ok, h) = \
					 self.send("TDevAcc.ReadTargetV('Amp1.cSnip~%d', 0, %d)" %
							   (n, self.sniplen*3))
				params[n, 'thresh'] = t
				params[n, 'hoops'] = h
			return params
		else:
			for n in range(1, self.nchans+1):
				t = params[n, 'thresh']
				h = params[n, 'hoops']

				(ok, r) = \
					 self.send("TDevAcc.SetTargetVal('Amp1.aSnip~%d',%f)" %
							   (n, t))
				(ok, r) = \
					 self.send("TDevAcc.WriteTargetVEX('Amp1.cSnip~%d', 0, 'F32', %s)" %
							   (n, h))
				self.send('type(%s)' % (h,))
			
if __name__ == '__main__':
	try:
		s = TDTServer()
	except ImportError:
		sys.stderr.write("Don't run me under linux!\n")
		sys.exit(0)
		
	try:
		s.listen()
	except:
		sys.stderr.write('\n\n')
		sys.stderr.write('Server-side fatal error in read-eval loop:\n')
		sys.stderr.write('%s\n' % sys.exc_value)
		sys.stderr.write('\n\n<hit return to close window and exit>')
		sys.stdin.readline()