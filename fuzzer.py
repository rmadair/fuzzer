from multiprocessing import Process, Queue
from threading import Thread
from optparse import OptionParser
from shutil import copy
from os import remove
from time import sleep, ctime
from sys import exit, argv

from Executor import Executor
from Mutator import Mutator

# todo
# - set signal handler to SIGINT, show status, give option to quit
# - maybe save progress and continue later, or at least allow a run offset
# - add timeout to command line options

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

		# print some useful information, and figure out some relative percentages
		mutator.print_statistics()
		ten_percent = mutator.total_mutations / 10
		percent     = 0

		for counter, (offset, value_index, value_type, new_file) in enumerate(mutator.createNext()):
			while not self.q_to.empty():
				sleep(.1)

			# check if we hit a 10% mark
			if counter % ten_percent == 0:
				print '%02d%% - %s' % (percent, ctime())
				percent += 10

			# add the job to the queue
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
		counter = 0

		while True:
			# wait for output
			obj = self.q_from.get()	# this blocks

			# poison pill
			if obj == 'STOP':
				break

			self.log.write('[%d] executable = %s, offset=%d, value_index=%d, value_type=%s, args=%s\n--------------------------------------\n' % (
				counter, obj['command'], obj['offset'], obj['value_index'], obj['value_type'], obj['args']))
			if obj['crash']:
				print 'Crash!'
				self.log.write(obj['output'])
				# save good files
				copy(obj['new_file'], self.save_directory)	

			remove("%s"%obj['new_file'])
			counter += 1

def check_usage(args):
    ''' Parse command line options - yes, these aren't really "options".... deal with it '''

    parser = OptionParser()
    parser.add_option('-p', action="store", dest="program_cmd_line", help='Program to launch, the full command line that will be executed', metavar="program")
    parser.add_option('-f', action="store", dest="original_file", help='File to be mutated', metavar="file")
    parser.add_option('-d', action="store", dest="temp_directory", help='Directory for temporary files to be created', metavar="temp_directory")
    parser.add_option('-t', action="store", dest="mutation_type", help='Type of mutation ("byte", "word", "dword")', metavar="mutation_type")
    parser.add_option('-l', action="store", dest="log_file", help='Log file', metavar="log")
    parser.add_option('-s', action="store", dest="save_directory", help='Save-directory, for files to be saved that cause crashes', metavar="save_directory")
    parser.add_option('-m', action="store", dest="max_processes", help='Max Processes (Default is 1)', type="int", default=1, metavar="max_processes")
    parser.epilog = "Example:\n\n"
    parser.epilog += './fuzzer.py -p "C:\Program Files\Blah\prog.exe" -f original_file.mp3 -d temp -t dword -l log.txt -s save -m 4'
    options, args = parser.parse_args(args)

    # make sure enough args are passed
    if not all((options.program_cmd_line, options.original_file, options.temp_directory, options.mutation_type, options.log_file, options.save_directory)):
        parser.error("Incorrect number of arguments - must specify program, original_file, temp_directory, mutation_type, log_file, save_directory")

    return options


if __name__ == '__main__':
    # check args, get args
    options = check_usage(argv)
    program_cmd_line = options.program_cmd_line
    original_file    = options.original_file
    temp_directory   = options.temp_directory
    mutation_type    = options.mutation_type
    log_file         = options.log_file
    save_directory   = options.save_directory
    max_processes    = options.max_processes

    # create the fuzzer, start it
    fuzzer = Fuzzer(max_processes, log_file, save_directory)
    fuzzer.start(program_cmd_line, original_file, 5, temp_directory, mutation_type)
