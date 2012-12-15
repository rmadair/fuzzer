# for twisted
from twisted.internet import protocol, reactor
from twisted.internet.protocol import ServerFactory
from twisted.protocols import amp
from time import time
import commands

# for mutations
from Mutator import MutationGenerator

from os.path import split
from sys import exit
from threading import Thread
from time import sleep, ctime

class FuzzerServerProtocol(amp.AMP):

    @commands.GetNextMutation.responder
    def getNextMutation(self):
        #print 'getNextMutation(...)'
        ret = self.factory.getNextMutation()
        return ret

    @commands.LogResults.responder
    def logResults(self, mutation_index, offset, output, filename):
        print 'Got a crash!'
        self.factory.log_file.write('Offset: %d, Mutation_Index: %d, Filename: %s, Output:\n%s'%
                (offset, mutation_index, filename, output))
        self.factory.crashes.append({'mutation_index':mutation_index, 'offset':offset, 'output':output, 'filename':filename})
        return {}

    @commands.GetOriginalFile.responder
    def getOriginalFile(self):
        #print 'getOringlaFile(...)'
        return {'original_file':self.factory.contents, 'original_file_name':self.factory.file_name}

    @commands.GetMutationTypes.responder
    def getMutationTypes(self):
        #print 'getMutationTypes(...)'
        return {'mutation_types':self.factory.mutations}

    @commands.GetProgram.responder
    def getProgram(self):
        #print 'getProgram(...)'
        return {'program':self.factory.program}

    def connectionMade(self):
        ''' add new clients to the list '''
        self.factory.clients.append(self.transport.getPeer())

    def connectionLost(self, traceback):
        ''' remove clients from the list '''
        self.factory.clients.remove(self.transport.getPeer())

class FuzzerFactory(ServerFactory):
    protocol = FuzzerServerProtocol

    def __init__(self, program, original_file, log_file_name):
        print 'FuzzerFactory(...) started'
        self.mutation_generator = MutationGenerator('byte')
        self.mutations          = self.mutation_generator.getValues()
        self.mutations_range    = range(len(self.mutations))
        self.file_name          = split(original_file)[1]       # just the filename
        self.program            = program
        self.log_file_name      = log_file_name                 # just the name
        self.log_file           = None                          # the opened instance
        self.contents           = None
        self.contents_range     = None
        self.generator          = self.createGenerator()
        self.clients            = []                            # list of clients
        self.crashes            = []                            # list of crashes
        self.mutations_executed = 0                             # number of mutations executed so far

        # make sure we can read the original target file
        try:
            self.contents = open(original_file, 'rb').read()
            self.contents_range = range(len(self.contents))
        except Exception as e:
            quit('Unable to open "%s" and read the contents. Error: %s' % (original_file, e))
    
        # make sure we can write to the logfile
        try:
            self.log_file = open(self.log_file_name, 'w')
        except Exception as e:
            quit('Unable to open logfile "%s". Error: %s' % (self.log_file_name, self.log_file))

        # a thread to handle user input and print statistics
        menu_thread = Thread(target=self.menu)
        menu_thread.start()
            
    def createGenerator(self):
        for offset in self.contents_range:
            for mutation_index in self.mutations_range:
                yield {'offset':offset, 'mutation_index':mutation_index, 'stop':False}

    def getNextMutation(self):
        try:
            n = self.generator.next()
            self.mutations_executed += 1
            return n
        except StopIteration:
            # no more mutations, close the logfile
            if not self.log_file.closed:
                self.log_file.close()
            # tell any clients to 'stop'
            return {'offset':0, 'mutation_index':0, 'stop':True}

    def printStatistics(self, mutations=False, clients=False, crashes=False):
        ''' print some statistics information '''

        print ''
        if mutations:
            total_mutations = len(self.contents) * len(self.mutations) 
            print 'Mutations:'
            print '  - File size                    :', len(self.contents)
            print '  - Number of possible mutations :', len(self.mutations)
            print '  - Total number of mutations    :', total_mutations
            print '  - Total executed so far        : %d (%d%%)' % (self.mutations_executed, float(self.mutations_executed)/total_mutations*100)
        if clients:
            print 'Clients:'
            for client in self.clients:
                print '  - %s:%d' % (client.host, client.port)
        if crashes:
            print 'Crashes:'
            for crash in self.crashes:
                print '  - Offset         :',   crash['offset']
                print '  - Mutation Index :',   crash['mutation_index']
                print '  - Filename       :',   crash['filename']
                print '  - Output         :\n', crash['output']

    def menu(self):
        while True:
            print '\n' 
            print 'Menu :'
            print '1. Show clients'
            print '2. Show crashes'
            print '3. Mutations'
            print '4. Show all'
            selection = raw_input('Enter Selection : ')
            if selection.strip() == '1':
                self.printStatistics(clients=True)
            if selection.strip() == '2':
                self.printStatistics(crashes=True)
            if selection.strip() == '3':
                self.printStatistics(mutations=True)
            if selection.strip() == '4':
                self.printStatistics(clients=True, crashes=True, mutations=True)

def quit(message=None):
    if message:
        print message
    print 'Exiting!'
    exit(1)

def main():
    #factory = FuzzerFactory(r'C:\windows\system32\calc.exe', r'C:\users\nomnom\infosec\fuzzing\git\testfile.txt', r'C:\users\nomnom\infosec\fuzzing\git\temp\logs\logfile.txt')
    factory = FuzzerFactory(r'a.exe', r'C:\users\nomnom\infosec\fuzzing\git\testfile.txt', r'C:\users\nomnom\infosec\fuzzing\git\temp\logs\logfile.txt')
    reactor.listenTCP(12345, factory)
    reactor.run()

if __name__ == '__main__':
    main()

