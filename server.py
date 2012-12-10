# for twisted
from twisted.internet import protocol, reactor
from twisted.internet.protocol import ServerFactory
from twisted.protocols import amp
from time import time
import commands

# for mutations
from Mutator import MutationGenerator

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

	def startFactory(self):
		print 'startFactory(...)'
		self.offset = 0
		self.mutation_generator = MutationGenerator('byte')

def main():
	factory = FuzzerFactory()
	reactor.listenTCP(12345, factory)
	reactor.run()

if __name__ == '__main__':
	main()

