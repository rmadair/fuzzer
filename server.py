# for twisted
from twisted.internet import protocol, reactor
from twisted.internet.protocol import ServerFactory
from twisted.protocols import amp
from time import time
import commands

# for mutations
from Mutator import MutationGenerator

from optparse import OptionParser
from os.path import split
from sys import argv, exit
from threading import Thread
from time import sleep, ctime

class FuzzerServerProtocol(amp.AMP):

    @commands.GetNextMutation.responder
    def getNextMutation(self):
        ret = self.factory.getNextMutation()
        return ret

    @commands.LogResults.responder
    def logResults(self, mutation_index, offset, output, filename):
        print 'Got a crash!'
        # log the crash
        self.factory.log_file.write('Offset: %d, Mutation_Index: %d, Filename: %s, Output:\n%s'%
                (offset, mutation_index, filename, output))
        self.factory.log_file.flush()
        # add it to the servers list
        self.factory.crashes.append({'mutation_index':mutation_index, 'offset':offset, 'output':output, 'filename':filename})
        return {}

    @commands.GetOriginalFile.responder
    def getOriginalFile(self):
        return {'original_file_name':self.factory.file_name, 'original_file':self.factory.contents}

    @commands.GetMutationTypes.responder
    def getMutationTypes(self):
        return {'mutation_types':self.factory.mutations}

    @commands.GetProgram.responder
    def getProgram(self):
        return {'program':self.factory.program}

    def connectionMade(self):
        ''' add new clients to the list '''
        self.factory.clients.append(self.transport.getPeer())

    def connectionLost(self, traceback):
        ''' remove clients from the list '''
        self.factory.clients.remove(self.transport.getPeer())

class FuzzerFactory(ServerFactory):
    protocol = FuzzerServerProtocol

    def __init__(self, program, original_file, log_file_name, mutation_type):
        print 'FuzzerFactory(...) started'
        self.mutation_generator = MutationGenerator(mutation_type)
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
        self.paused             = False

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
                yield {'offset':offset, 'mutation_index':mutation_index, 'stop':False, 'pause':False}

    def getNextMutation(self):
        if self.paused:
            return {'offset':0, 'mutation_index':0, 'stop':False, 'pause':True}
        try:
            n = self.generator.next()
            self.mutations_executed += 1
            return n
        except StopIteration:
            # no more mutations, close the logfile
            if not self.log_file.closed:
                self.log_file.close()
            # tell any clients to 'stop'
            return {'offset':0, 'mutation_index':0, 'stop':True, 'pause':False}

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
            if self.paused: print '---- PAUSED ----'
            print 'Menu :'
            print '1. Show clients'
            print '2. Show crashes'
            print '3. Mutations'
            print '4. Show all'
            print '5. Pause/Resume'
            selection = raw_input('Enter Selection : ').rstrip()
            if selection == '1':
                self.printStatistics(clients=True)
            if selection == '2':
                self.printStatistics(crashes=True)
            if selection == '3':
                self.printStatistics(mutations=True)
            if selection == '4':
                self.printStatistics(clients=True, crashes=True, mutations=True)
            if selection == '5':
                self.paused = False if self.paused else True

def quit(message=None):
    if message:
        print message
    print 'Exiting!'
    exit(1)

def check_usage(args):
    ''' Parse command line - they're not really optional, shhh'''

    parser = OptionParser()
    parser.add_option('-e', action="store", dest="program_cmd_line", help='Executable program to launch, the full command line that will be executed', metavar="program")
    parser.add_option('-f', action="store", dest="original_file", help='File to be mutated', metavar="file")
    parser.add_option('-t', action="store", dest="mutation_type", help='Type of mutation ("byte", "word", "dword")', metavar="mutation_type")
    parser.add_option('-l', action="store", dest="log_file", help='Log file', metavar="log")
    parser.add_option('-p', action="store", dest="port", help='Port to listen on', type='int', metavar="port")
    parser.epilog = "Example:\n\n"
    parser.epilog += './server.py -e "C:\Program Files\Blah\prog.exe" -f original_file.mp3 -t dword -l log.txt -p 12345'
    options, args = parser.parse_args(args)

    # make sure enough args are passed
    if not all((options.program_cmd_line, options.original_file, options.mutation_type, options.log_file, options.port)):
        parser.error("Incorrect number of arguments - must specify program, original_file, mutation_type, log_file, port")

    return options

if __name__ == '__main__':
    options = check_usage(argv)
    factory = FuzzerFactory(options.program_cmd_line, options.original_file, options.log_file, options.mutation_type)
    reactor.listenTCP(options.port, factory)
    reactor.run()

