from twisted.internet import reactor, endpoints, protocol
from twisted.internet.task import LoopingCall
from twisted.protocols import amp
import commands

def stop(reason):
    print 'Stopping :', reason
    reactor.stop()

class FuzzerClientProtocol(amp.AMP):
    def executeNextMutation(self, mutation):
        print 'got mutation:', mutation 
        if mutation['stop']:
            stop("Server said to stop")
        # perform all the work in here
        # ...
        # faking a message to be logged back at the server side
        if mutation['offset'] % 10 == 0:
            self.callRemote(
                commands.CommandThree,
                arg1="logging a message on mutation %(offset)d" % mutation)
            print 'sending a message back to the server'

    def getNextMutation(self):
        (self.callRemote(commands.CommandOne)
         .addCallback(self.executeNextMutation)
         .addErrback(stop))

    def connectionMade(self):
        self.lc = LoopingCall(self.getNextMutation)
        self.lc.start(0.1)

class FuzzerClientFactory(protocol.ClientFactory):
    protocol = FuzzerClientProtocol
        
def main():
    (endpoints.TCP4ClientEndpoint(reactor, '127.0.0.1', 12345)
     .connect(FuzzerClientFactory())
     .addErrback(stop))
    reactor.run()

main()

