from multiprocessing import Process, Queue
from threading import Thread
from shutil import copy
from os import remove
from time import sleep, time
from sys import exit

from Executor import Executor
from Mutator import Mutator

class Fuzzer():
	def __init__(self, max_processes, logfile, save_directory):
		self.q_to = Queue()
		self.q_from = Queue()
		self.processes = []
		self.max_processes = max_processes
		self.save_directory = save_directory
		self.mutator = None
		self.monitor_thread = None

		# open the logfile
		try:
			log = open(logfile, 'w')
		except:
			print '[!] Unable to open logfile', logfile
			exit(1)
		self.log = log

		
	def start(self, command, original_file, timeout, temp_directory, mutation_type):
		# create the consumers
		for i in range(self.max_processes):
			process = Process(target=Executor, args=(timeout, self.q_to, self.q_from))
			self.processes.append(process)
			process.start()

		# create the thread to get consumer output
		self.monitor_thread = Thread(target=self.monitor)
		self.monitor_thread.start()

		# create the mutator
		mutator = Mutator(original_file, temp_directory, mutation_type)

		for counter, (offset, value_index, value_type, new_file) in enumerate(mutator.createNext()):
			while not self.q_to.empty():
				sleep(.1)

			self.q_to.put({'command':command, 'args':'%s'%new_file, 'offset':offset, 'value_index':value_index, 'value_type':value_type, 'new_file':new_file})

		self.stop()
	
	def stop(self):
		# kill the consumers
		for i in range(self.max_processes):
			self.q_to.put('STOP')
		for process in self.processes:
			process.join()
		# kill the monitor thread
		self.q_from.put('STOP')
		self.monitor_thread.join()
		# close the log file
		self.log.close()

	def monitor(self):
		while True:
			# wait for output
			obj = self.q_from.get()	# this blocks

			# poison pill
			if obj == 'STOP':
				break

			self.log.write('executable = %s, offset=%d, value_index=%d, value_type=%s, args=%s\n--------------------------------------\n' % (
				obj['command'], obj['offset'], obj['value_index'], obj['value_type'], obj['args']))
			if obj['crash']:
				print 'Crash!'
				self.log.write(obj['output'])
				# save good files
				copy(obj['new_file'], self.save_directory)	
			remove(obj['new_file'])

if __name__ == '__main__':
	fuzzer = Fuzzer(3, 'logfile.txt-%d'%time(), r'C:\Users\nomnom\utdcsg\fuzzing\save')	
	fuzzer.start(r'"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"', r'C:\Users\nomnom\utdcsg\fuzzing\sample_3gp_files\sample.nuv', 5, r'C:\Users\nomnom\utdcsg\fuzzing\temp', 'dword')
