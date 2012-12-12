# for twisted
from twisted.internet import reactor, endpoints, protocol
from twisted.internet.task import LoopingCall
from twisted.protocols import amp
import commands

# for pydbg execution
from pydbg import *
from pydbg.defines import *
import utils

# for mutations and execution
from Mutator import Mutator


def stop(reason):
    ''' Generic function to stop the reactor  and print a message '''
    print 'Stopping :', reason
    reactor.stop()

class FuzzerClientProtocol(amp.AMP):

    def __init__(self):
        self.original_file 	= None
        self.mutation_types = None
        self.mutator 	   	= None

    def connectionMade(self):
        # get original file to work with
        self.getOriginalFile()

        # get the list of mutations we will be working with
        self.getMutationTypes()

        # we have all the pieces the mutator needs
        self.mutator = Mutator(self.original_file, self.mutation_types)

        # enter continuous loop
        self.lc = LoopingCall(self.getNextMutation)
        self.lc.start(0.1)


    def getNextMutation(self):
        ''' Ask the server for the next mutation '''
        (self.callRemote(commands.GetNextMutation)
         .addCallback(self.executeNextMutation)
         .addErrback(stop))

    def executeNextMutation(self, mutation):
        print '- got mutation:', mutation 
        if mutation['stop']:
            stop("Server said to stop")

		# create the mutated file
		#self.mutator.createMutatedFile(
        # ...
        # faking a message to be logged back at the server side
        if mutation['offset'] % 10 == 0:
            self.callRemote( commands.LogResults, results="logging a message on mutation %(offset)d" % mutation)
            print 'sending a message back to the server'

    # getting list of mutations, and saving them
    def getMutationTypes(self):
        self.callRemote(commands.GetMutationTypes).addCallback(self.gotMutationTypes).addErrback(stop)
    def gotMutationTypes(self, response):
		print '[*] Got mutation types'
		self.mutation_types = response['mutation_types']

    # getting original file, and saving it
    def getOriginalFile(self):
        self.callRemote(commands.GetOriginalFile).addCallback(self.gotOriginalFile).addErrback(stop)
    def gotOriginalFile(self, response):
        print '[*] Got original_file'
        self.original_file = response['original_file']

class FuzzerClientFactory(protocol.ClientFactory):
    protocol = FuzzerClientProtocol
        
def main():
    (endpoints.TCP4ClientEndpoint(reactor, '127.0.0.1', 12345)
     .connect(FuzzerClientFactory())
     .addErrback(stop))
    reactor.run()

main()

