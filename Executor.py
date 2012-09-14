from pydbg import *
from pydbg.defines import *
from time import time, sleep
import utils

class Executor():
	def __init__(self, timeout, queue_in, queue_out):
		self.timeout   = timeout
		self.queue_in  = queue_in
		self.queue_out = queue_out
		self.obj       = None
		self.enterLoop()

	def enterLoop(self):
		while True:
			try:
				obj = self.queue_in.get_nowait()
			except:
				sleep(.1)
				continue

			if obj == 'STOP':
				break

			self.obj = obj
			self.execute(obj)

			if not 'crash' in self.obj:
				self.obj['crash'] = False
				self.obj['output'] = None

			self.queue_out.put(self.obj)

	def execute(self, q):
		dbg = pydbg()
		dbg.set_callback(EXCEPTION_ACCESS_VIOLATION, self.handle_av)
		dbg.set_callback(0xC000001D, self.handle_av) # illegal instruction
		dbg.set_callback(USER_CALLBACK_DEBUG_EVENT, self.timeout_callback)
		dbg.load(q['command'], command_line=q['args'])
		dbg.start_time = time()
		dbg.run()

	def timeout_callback(self, dbg):
		if time() - dbg.start_time > self.timeout:
			dbg.terminate_process()
			return DBG_CONTINUE

	def handle_av(self, dbg):
		crash_bin = utils.crash_binning.crash_binning()
		crash_bin.record_crash(dbg)
		self.obj['crash'] = True
		self.obj['output'] = crash_bin.crash_synopsis()

		dbg.terminate_process()
		return DBG_EXCEPTION_NOT_HANDLED
