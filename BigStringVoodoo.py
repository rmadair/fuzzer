''' the twisted guys are crazy, here is some of their voodoo to send a whole file at once ;) '''
from twisted.protocols import amp
import itertools

def split_string(x, size):
    return list(x[i*size:(i+1)*size] for i in xrange((len(x)+size-1)//size))

class StringList(amp.Argument):
    def fromBox(self, name, strings, objects, proto):
        objects[name] = list(itertools.takewhile(bool, (strings.pop('%s.%d' % (name, i), None) for i in itertools.count())))
    def toBox(self, name, strings, objects, proto):
        for i, elem in enumerate(objects.pop(name)):
            strings['%s.%d' % (name, i)] = elem

class BigString(StringList):
    def fromBox(self, name, strings, objects, proto):
        StringList.fromBox(self, name, strings, objects, proto)
        objects[name] = ''.join((elem) for elem in objects[name])
    def toBox(self, name, strings, objects, proto):
        objects[name] = split_string(objects[name], amp.MAX_VALUE_LENGTH)
        StringList.toBox(self, name, strings, objects, proto)
