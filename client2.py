# for twisted
from twisted.internet import reactor, endpoints, protocol, defer
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
        self.original_file = None
        self.original_file_name = None
        self.mutation_types = None
        self.mutator = None

    def connectionMade(self):
        setupDeferreds = [self.getOriginalFile(), self.getMutationTypes()]
        defer.gatherResults(setupDeferreds).addCallback(self.finishSetup).addErrback(stop)

    def finishSetup(self, ign):
        # we have all the pieces the mutator needs
        self.mutator = Mutator(
            self.original_file, self.mutation_types, self.original_file_name, self.factory.tmp_directory)

        # enter continuous loop
        self.lc = LoopingCall(self.getNextMutation)
        self.lc.start(0.1)

    def getNextMutation(self):
        ''' Ask the server for the next mutation '''
        return (self.callRemote(commands.GetNextMutation)
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
    @defer.inlineCallbacks
    def getMutationTypes(self):
        response = yield self.callRemote(commands.GetMutationTypes)
        print '[*] Got mutation types'
        self.mutation_types = response['mutation_types']

    # getting original file, and saving it
    @defer.inlineCallbacks
    def getOriginalFile(self):
        response = yield self.callRemote(commands.GetOriginalFile)
        print '[*] Got original_file,', response['original_file_name']
        self.original_file = response['original_file']
        self.original_file_name = response['original_file_name']

class FuzzerClientFactory(protocol.ClientFactory):
    protocol = FuzzerClientProtocol

    def __init__(self, tmp_directory):
        self.tmp_directory = tmp_directory
        
def main():
    (endpoints.TCP4ClientEndpoint(reactor, '127.0.0.1', 12345)
     .connect(FuzzerClientFactory(r'C:\users\nomnom\infosec\fuzzing\git\temp\testing'))
     .addErrback(stop))
    reactor.run()

main()

