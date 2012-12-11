# for twisted
from twisted.internet import protocol, reactor
from twisted.internet.protocol import ServerFactory
from twisted.protocols import amp
from time import time
import commands

# for mutations
from Mutator import MutationGenerator

from sys import exit

class FuzzerServerProtocol(amp.AMP):

	@commands.GetNextMutation.responder
	def getNextMutation(self):
		print 'commandOne(...)'
		ret = self.factory.getNextMutation()
		print ret
		return ret
		#return {'offset':self.factory.offset, 'mutation_index':42, 'stop':False}

	@commands.LogResults.responder
	def logResults(self, results):
		print 'logResults(%s)' % results 
		return {}

	@commands.GetOriginalFile.responder
	def getOriginalFile(self):
		print 'getOringlaFile(...)'
		return {'original_file':'BBB\xab\x00\xcdAAA'}

	@commands.GetMutationTypes.responder
	def getMutationTypes(self):
		print 'getMutationTypes(...)'
		return {'mutation_types':self.factory.mutations}
		#return {'mutation_types':[{'value':'\xde\xad\xbe\xef', 'offset':42, 'type':'string', 'size':1}, {'value':'\xde\xad\xbe\xef', 'offset':43, 'type':'string', 'size':1}]}


class FuzzerFactory(ServerFactory):
	protocol = FuzzerServerProtocol

	def __init__(self, original_file):
		print 'FuzzerFactory(...) started'
		self.mutation_generator = MutationGenerator('byte')
		self.mutations			= self.mutation_generator.getValues()
		self.mutations_range	= range(len(self.mutations))
		self.contents 		    = None
		self.contents_range		= None
		self.generator 			= self.createGenerator()

		# make sure we can read the original target file
		try:
			self.contents = open(original_file, 'rb').read()
			self.contents_range = range(len(self.contents))
		except:
			print 'Unable to open "%s" and read the contents. Exiting!' % original_file
			exit(1) 
            
	def createGenerator(self):
		for offset in self.contents_range:
			for mutation_index in self.mutations_range:
				yield {'offset':offset, 'mutation_index':mutation_index, 'stop':False}

	def getNextMutation(self):
		return self.generator.next()

def main():
	factory = FuzzerFactory(r'C:\users\nomnom\infosec\fuzzing\git\server-demo.py')
	reactor.listenTCP(12345, factory)
	reactor.run()

if __name__ == '__main__':
	main()

