from twisted.internet import protocol, reactor
from twisted.internet.protocol import ServerFactory
from twisted.protocols import amp
from time import time
import commands

class FuzzerServerProtocol(amp.AMP):

	@commands.CommandOne.responder
	def commandOne(self):
		print 'commandOne(...)'
		return {'offset':self.factory.my_list.pop(), 'value':42, 'stop':False}

	@commands.CommandTwo.responder
	def commandTwo(self, arg1, arg2):
		print 'commandTwo(...)'
		return {"outputTwo":arg1+arg2}

	@commands.CommandThree.responder
	def commandThree(self, arg1):
		print 'commandThree(%s)' % arg1
		return {}

class FuzzerFactory(ServerFactory):
	protocol = FuzzerServerProtocol

	def startFactory(self):
		print 'startFactory(...)'
		self.my_list = range(1000)

def main():
	factory = FuzzerFactory()
	reactor.listenTCP(12345, factory)
	reactor.run()

if __name__ == '__main__':
	main()

