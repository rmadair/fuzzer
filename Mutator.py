import struct
import os
from sys import exit

MAX8  = 0xff
MAX16 = 0xffff
MAX32 = 0xffffffff

#values_8bit  = [0x00, 0x01, MAX8/2-16,  MAX8/2-1,  MAX8/2,  MAX8/2+1,  MAX8/2+16,  MAX8-16,  MAX8-1,  MAX8]
#values_16bit = [0x00, 0x01, MAX16/2-16, MAX16/2-1, MAX16/2, MAX16/2+1, MAX16/2+16, MAX16-16, MAX16-1, MAX16]
#values_32bit = [0x00, 0x01, MAX32/2-16, MAX32/2-1, MAX32/2, MAX32/2+1, MAX32/2+16, MAX32-16, MAX32-1, MAX32]

values_8bit  = [{'value':0x00,       'type':'replace', 'size':1}, {'value':0x01,    'type':'replace', 'size':1}, {'value':MAX8/2-16,  'type':'replace', 'size':1}, 
                {'value':MAX8/2-1,   'type':'replace', 'size':1}, {'value':MAX8/2,  'type':'replace', 'size':1}, {'value':MAX8/2+1,   'type':'replace', 'size':1}, 
                {'value':MAX8/2+16,  'type':'replace', 'size':1}, {'value':MAX8-1,  'type':'replace', 'size':1}, {'value':MAX8,       'type':'replace', 'size':1} ]

values_16bit  = [{'value':0x00,      'type':'replace', 'size':2}, {'value':0x01,    'type':'replace', 'size':2}, {'value':MAX16/2-16, 'type':'replace', 'size':2}, 
                {'value':MAX16/2-1,  'type':'replace', 'size':2}, {'value':MAX16/2, 'type':'replace', 'size':2}, {'value':MAX16/2+1,  'type':'replace', 'size':2}, 
                {'value':MAX16/2+16, 'type':'replace', 'size':2}, {'value':MAX16-1, 'type':'replace', 'size':2}, {'value':MAX16,      'type':'replace', 'size':2} ]

values_32bit  = [{'value':0x00,       'type':'replace', 'size':4}, {'value':0x01,    'type':'replace', 'size':4}, {'value':MAX32/2-16, 'type':'replace', 'size':4}, 
                {'value':MAX32/2-1,  'type':'replace', 'size':4}, {'value':MAX32/2, 'type':'replace', 'size':4}, {'value':MAX32/2+1,  'type':'replace', 'size':4}, 
                {'value':MAX32/2+16, 'type':'replace', 'size':4}, {'value':MAX32-1, 'type':'replace', 'size':4}, {'value':MAX32,      'type':'replace', 'size':4} ]
values_strings = [{'value':list("B"*100),  'type':'insert', 'size':100}, \
                  {'value':list("B"*1000), 'type':'insert', 'size':1000}, \
                  {'value':list("B"*10000),'type':'insert', 'size':10000}, \
                  {'value':list("%s"*10),  'type':'insert', 'size':10}, \
                  {'value':list("%s"*100), 'type':'insert', 'size':100}]




    

class Mutator():
    ''' Mutator itterates over the contents of a given file, and using values from ValueGenerator, mutates
        the given file, creating a new one. '''

    def __init__(self, value_type):
        ValueGenerator.__init__(self, value_type=value_type)
        self.value_type         = value_type

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

class MutationGenerator():

    def __init__(self, value_type, strings=True):
        self.generateValues(value_type, strings)

    def generateValues(self, value_type, strings):
        global values_8bit
        global values_16bit
        global values_32bit
        global values_string
        values = []
        if value_type == 'byte':
            values.extend(values_8bit)
        elif value_type == 'word':
            values.extend(values_16bit)
        elif value_type == 'dword':
            values.extend(values_32bit)
        else:
            raise Exception('unknown value type passed to generateValues(...), %s' % value_type)

        if strings:
            values.extend(values_strings)

        # turn them into writeable bytes
        self.value_to_bytes(values, vtype=value_type)
        self.createWriteable(values)
        self.values = values

    def value_to_bytes(self, values, vtype='dword'):
        '''Given a value as an int, return it in little endian bytes of length type.
           Example, given 0xabcdeff with type "dword" : (255, 222, 188, 10) '''
        for value_dict in values:
            if value_dict['type'] == 'insert':
                continue
            value = value_dict['value']
            try:
                if vtype == 'byte':
                        value_dict['value'] = list(struct.unpack('B', struct.pack('B', value)))
                elif vtype == 'word':
                        value_dict['value'] = list(struct.unpack('BB', struct.pack('<H', value)))
                elif vtype == 'dword':
                        value_dict['value'] = list(struct.unpack('BBBB', struct.pack('<I', value)))
            except:
                print 'value =', value
                exit(1)


    def createWriteable(self, values):     
        ''' When writting to a file, a string is required. This function itterates over
            all values generated, and turns any int values into their representative char. '''

        for value_dict in values:                                       # get each dictionary
            for offset, value in enumerate(value_dict['value']):        # go through each of the indexes in the 'value' 
                if type(value) == int:                                  # if it's an int
                    value_dict['value'][offset] = chr(value)            # turn it into it's char representation

    def getValues(self):
        return self.values
