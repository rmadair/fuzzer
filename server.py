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

	@commands.CommandOne.responder
	def commandOne(self):
		print 'commandOne(...)'
		return {'offset':self.factory.offset, 'value':42, 'stop':False}

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
		return {'mutation_types':[{'value':'\xde\xad\xbe\xef', 'offset':42, 'type':'string', 'size':1}, {'value':'\xde\xad\xbe\xef', 'offset':43, 'type':'string', 'size':1}]}


class FuzzerFactory(ServerFactory):
	protocol = FuzzerServerProtocol

	def __init__(self, original_file):
		print 'FuzzerFactory(...) started'
		self.offset 			= 0
		self.mutation_generator = MutationGenerator('byte')
		self.contents 		    = None
		self.contents_len		= None

		# make sure we can read the original target file
		try:
			self.contents = open(original_file, 'rb').read()
			self.contents_len = len(self.contents)
		except:
			print 'Unable to open "%s" and read the contents. Exiting!' % original_file
			exit(1)

	def getNextMutation(self):

		#### MAKE THIS A GENERATOR THAT RETURNS THE NEXT MUTATION - tada :)

def main():
	factory = FuzzerFactory(r'C:\users\nomnom\infosec\fuzzing\git\server-demo.py')
	reactor.listenTCP(12345, factory)
	reactor.run()

if __name__ == '__main__':
	main()

