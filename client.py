# for twisted
from twisted.internet import reactor, endpoints, protocol, defer
from twisted.internet.task import LoopingCall
from twisted.protocols import amp
import commands

# for mutations and execution
from Executor import Executor
from Mutator import Mutator

from os import remove
from os.path import join, split
from shutil import copy

def stop(reason):
    ''' Generic function to stop the reactor  and print a message '''
    print 'Stopping :', reason
    # try to stop the reactor, may or may not be running
    try:
        reactor.stop()
    except:
        pass

class FuzzerClientProtocol(amp.AMP):

    def __init__(self):
        self.executor = Executor()
        self.original_file = None
        self.original_file_name = None
        self.mutation_types = None
        self.program = None
        self.mutator = None

    def connectionMade(self):
        setupDeferreds = [self.getOriginalFile(), self.getProgram(), self.getMutationTypes()]
        defer.gatherResults(setupDeferreds).addCallback(self.finishSetup).addErrback(stop)

    def finishSetup(self, ign):
        # we have all the pieces the mutator needs
        self.mutator = Mutator(
            self.original_file, self.mutation_types, self.original_file_name, self.factory.tmp_directory)

        # enter continuous loop
        self.lc = LoopingCall(self.getNextMutation)
        self.lc.start(0)

    def getNextMutation(self):
        ''' Ask the server for the next mutation '''
        return (self.callRemote(commands.GetNextMutation) # return deferred
                .addCallback(self.executeNextMutation)
                .addErrback(stop))

    def executeNextMutation(self, mutation):
        if mutation['stop']:
            stop("Server said to stop")
            return False

        # create the mutated file
        new_file_name = self.mutator.createMutatedFile(mutation['offset'], mutation['mutation_index'])

        # execute it
        print '(%d,%d)' % (mutation['offset'], mutation['mutation_index']),
        output = self.executor.execute(self.program, new_file_name)
        if output:
            print 'Got output, Offset = %d, Mutation_Index = %d, File = %s' % (mutation['offset'], mutation['mutation_index'], new_file_name)
            self.callRemote( commands.LogResults, mutation_index=mutation['mutation_index'], offset=mutation['offset'], output=output, filename=new_file_name )
            # copy the file - it caused a crash
            copy("%s"%new_file_name, "%s"%join(self.factory.save_directory, split(new_file_name)[-1]))

        # remove the file
        remove("%s"%new_file_name)

    @defer.inlineCallbacks
    def getOriginalFile(self):
        ''' get original file and file name'''
        response = yield self.callRemote(commands.GetOriginalFile)
        print '[*] Got original_file :', response['original_file_name']
        self.original_file = response['original_file']
        self.original_file_name = response['original_file_name']

    @defer.inlineCallbacks
    def getMutationTypes(self):
        ''' get list of mutations that will be used '''
        response = yield self.callRemote(commands.GetMutationTypes)
        print '[*] Got mutation types'
        self.mutation_types = response['mutation_types']

    @defer.inlineCallbacks
    def getProgram(self):
        ''' get target program that will be executed '''
        response = yield self.callRemote(commands.GetProgram)
        print '[*] Got program :', response['program']
        self.program = response['program']

class FuzzerClientFactory(protocol.ClientFactory):
    protocol = FuzzerClientProtocol

    def __init__(self, tmp_directory, save_directory):
        self.tmp_directory  = tmp_directory
        self.save_directory = save_directory
        
def main():
    (endpoints.TCP4ClientEndpoint(reactor, '127.0.0.1', 12345)
     .connect(FuzzerClientFactory(r'C:\users\nomnom\infosec\fuzzing\git\temp\testing', r'C:\users\nomnom\infosec\fuzzing\git\temp\save'))
     .addErrback(stop))
    reactor.run()

main()

