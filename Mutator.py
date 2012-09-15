import struct
import os
from sys import exit

# todo
#
# get rid of this global crap, define it in ValueGenerator

MAX8  = 0xff
MAX16 = 0xffff
MAX32 = 0xffffffff

values_8bit  = [0x00, 0x01, MAX8/2-16,  MAX8/2-1,  MAX8/2,  MAX8/2+1,  MAX8/2+16,  MAX8-16,  MAX8-1,  MAX8]
values_16bit = [0x00, 0x01, MAX16/2-16, MAX16/2-1, MAX16/2, MAX16/2+1, MAX16/2+16, MAX16-16, MAX16-1, MAX16]
values_32bit = [0x00, 0x01, MAX32/2-16, MAX32/2-1, MAX32/2, MAX32/2+1, MAX32/2+16, MAX32-16, MAX32-1, MAX32]
values_strings = [{'value':list("B"*100),  'type':'insert', 'size':100}, \
                  {'value':list("B"*1000), 'type':'insert', 'size':1000}, \
                  {'value':list("B"*10000),'type':'insert', 'size':10000}, \
                  {'value':list("%s"*10),  'type':'insert', 'size':10}, \
                  {'value':list("%s"*100), 'type':'insert', 'size':100}]


class ValueGenerator():
    ''' ValueGenerator is responsible for coming up with a list of values to be tested. Current possibilities
        include bytes, words, dwords and strings. A list of dictionaries is created by ValueGenerator in the form :

        [ {'value':0xff, 'size':1, 'type':replace}, ..., {'value':'BBB...B', 'size':None, 'type':'insert'}, ]

        'value' contains the actual value generated
        'size' contains the size of the value, in bytes
        'type' contains either 'insert' or 'replace'. 'insert' means the value will be inserted at a specific position, moving
               the rest of the contents over. 'replace' means the value is to overwrite the contents in the specific position, as
               typical "slider" mutators work
    '''

    def __init__(self, value_type, strings=True):
        global values_8bit
        global values_16bit
        global values_32bit
        self.values = values_strings if strings else [] # initially contain the strings. unless told otherwise, then start with an empty list
        # create a list of dictionaries, one per value. keys are 'value', 'size' and 'type' 
        if value_type == 'byte':
            self.values.extend( map(lambda x: {'value':self.value_to_bytes(x, vtype='byte'), 'size':1, 'type':'replace'}, values_8bit) )
        elif value_type == 'word':
            self.values.extend( map(lambda x: {'value':self.value_to_bytes(x, vtype='word'), 'size':2, 'type':'replace'}, values_16bit) )
        elif value_type == 'dword':
            self.values.extend( map(lambda x: {'value':self.value_to_bytes(x, vtype='dword'), 'size':4, 'type':'replace'}, values_32bit) )
        else:
            raise Exception('unknown value type passed to ValueGenerator, %s' % value_type)

        # turn them into writeable bytes
        self.createWriteable(self.values)

    def value_to_bytes(self, value, vtype='dword'):
        '''Given a value as an int, return it in little endian bytes of length type.
           Example, given 0xabcdeff with type "dword" : (255, 222, 188, 10) '''
        if vtype == 'byte':
                return list(struct.unpack('B', struct.pack('B', value)))
        elif vtype == 'word':
                return list(struct.unpack('BB', struct.pack('<H', value)))
        elif vtype == 'dword':
                return list(struct.unpack('BBBB', struct.pack('<I', value)))

    def createWriteable(self, new_bytes):     
        ''' When writting to a file, a string is required. This function itterates over
            all values generated, and turns any int values into their representative char. '''

        for value_dict in self.values:                                  # get each dictionary
            for offset, value in enumerate(value_dict['value']):        # go through each of the indexes in the 'value' 
                if type(value) == int:                                  # if it's an int
                    value_dict['value'][offset] = chr(value)            # turn it into it's char representation

    def getValues(self):
        return self.values

class Mutator(ValueGenerator):
    ''' Mutator itterates over the contents of a given file, and using values from ValueGenerator, mutates
        the given file, creating a new one. '''

    def __init__(self, original_file, tmp_directory, value_type):
        ValueGenerator.__init__(self, value_type=value_type)
        self.original_file      = original_file
        self.tmp_directory      = tmp_directory
        self.value_type         = value_type
        self.original_bytes     = None
        self.original_bytes_len = None
        self.mutated_file_num   = 0

        self.original_file_base = os.path.split(original_file)[-1]                # get the full file name
        self.original_file_base = os.path.splitext(self.original_file_base)[0]    # get the file base
        self.original_file_ext  = os.path.splitext(original_file)[1]              # get the file extention

        self.total_mutations    = None

        # get the contents of the original file
        #try:
        fopen = open(self.original_file, 'rb')
        self.original_bytes = fopen.read()
        self.original_bytes_len = len(self.original_bytes)
        self.total_mutations    = self.original_bytes_len * len(self.values)
        fopen.close()
        #except:
        #    raise Exception('[*] Mutator unable to open original_file %s' % self.original_file)

    def createNext(self):
        ''' Yield a tuple (offset, value, type, mutated_file_name) '''

        for offset in range(self.original_bytes_len):
            for value in self.getValues():
                new_bytes = list(self.original_bytes[:])
                if value['type'] == 'replace':
                    new_bytes[offset:offset+value['size']] = value['value']                 # if 'replace', then just substitute/replace the desired bytes
                elif value['type'] == 'insert':
                    new_bytes = new_bytes[:offset] + value['value'] + new_bytes[offset:]    # if 'insert', stick them in, shifting the rest of the bytes down
                else:
                     raise Exception('[*] UNKNOWN VALUE[\'TYPE\'], %s' % value['type'])

                #try:
                mutated_file_name = "%s-%d%s" % (self.original_file_base, self.mutated_file_num, self.original_file_ext)
                mutated_file_name = os.path.join(self.tmp_directory, mutated_file_name)
                self.mutated_file_num += 1
                fopen = open(mutated_file_name, 'wb')
                fopen.write( ''.join(new_bytes) ) 
                fopen.close()
                yield (offset, self.values.index(value), value['type'], mutated_file_name)
                #except:
                #    raise Exception('[*] unable to open tmp file for mutation! %s '%mutated_file_name)

    def print_statistics(self):
        ''' print some generic output with statistic information '''
        print '[*] File size                    :', self.original_bytes_len
        print '[*] Number of possible mutations :', len(self.getValues())
        print '[*] Total number of putations    :', self.total_mutations
