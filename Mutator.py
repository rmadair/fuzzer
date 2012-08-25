import struct
import os

MAX8  = 0xff
MAX16 = 0xffff
MAX32 = 0xffffffff

values_8bit  = [0x00, 0x01, MAX8/2-16,  MAX8/2-1,  MAX8/2,  MAX8/2+1,  MAX8/2+16,  MAX8-16,  MAX8-1,  MAX8]
values_16bit = [0x00, 0x01, MAX16/2-16, MAX16/2-1, MAX16/2, MAX16/2+1, MAX16/2+16, MAX16-16, MAX16-1, MAX16]
values_32bit = [0x00, 0x01, MAX32/2-16, MAX32/2-1, MAX32/2, MAX32/2+1, MAX32/2+16, MAX32-16, MAX32-1, MAX32]
values_strings = [{'value':list("A"*100),  'type':'insert', 'size':None}, \
                  {'value':list("A"*1000), 'type':'insert', 'size':None}, \
                  {'value':list("A"*10000),'type':'insert', 'size':None}, \
                  {'value':list("%s"*10),  'type':'insert', 'size':None}, \
                  {'value':list("%s"*100), 'type':'insert', 'size':None}]


class ValueGenerator():
    def __init__(self, value_type, strings=True):
        global values_8bit
        global values_16bit
        global values_32bit
        self.values = values_strings if strings else [] # initially contain the strings. unless told otherwise, then start with an empty list
        if value_type == 'byte':
            self.values.extend( map(lambda x: {'value':self.value_to_bytes(x, vtype='byte'), 'size':1, 'type':'replace'}, values_8bit) )
        elif value_type == 'word':
            self.values.extend( map(lambda x: {'value':self.value_to_bytes(x, vtype='word'), 'size':2, 'type':'replace'}, values_16bit) )
        elif value_type == 'dword':
            self.values.extend( map(lambda x: {'value':self.value_to_bytes(x, vtype='dword'), 'size':4, 'type':'replace'}, values_32bit) )
        else:
            raise Exception('unknown value type passed to ValueGenerator, %s' % value_type)

    def value_to_bytes(self, value, vtype='dword'):
        '''Given a value as an int, return it in little endian bytes of length type.
           Example, given 0xabcdeff with type "dword" : (255, 222, 188, 10) '''
        if vtype == 'byte':
                return list(struct.unpack('B', struct.pack('B', value)))
        elif vtype == 'word':
                return list(struct.unpack('BB', struct.pack('<H', value)))
        elif vtype == 'dword':
                return list(struct.unpack('BBBB', struct.pack('<I', value)))

    def getValues(self):
        return self.values

class Mutator():
    def __init__(self, original_file, tmp_directory, value_type):
        self.original_file      = original_file
        self.tmp_directory      = tmp_directory
        self.value_type         = value_type
        self.original_bytes     = None
        self.original_bytes_len = None
        self.mutated_file_num   = 0

        self.original_file_base = os.path.split(original_file)[-1]                # get the full file name
        self.original_file_base = os.path.splitext(self.original_file_base)[0]    # get the file base
        self.original_file_ext  = os.path.splitext(original_file)[1]              # get the file extention

        self.value_generator    = ValueGenerator(value_type=value_type)
        self.total_mutations    = None

        # get the contents of the original file
        try:
            fopen = open(self.original_file, 'r')
            self.original_bytes = fopen.read()
            self.original_bytes_len = len(self.original_bytes)
            self.total_mutations    = self.original_bytes_len * len(self.value_generator.values)
            fopen.close()
        except:
            raise Exception('[*] Mutator unable to open original_file')

    def createNext(self):
        for offset in range(self.original_bytes_len):
            for value in self.value_generator.getValues():
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
                self.createWriteable(new_bytes)
                fopen.write( ''.join(new_bytes) ) #### SHOULD CALL CREATEWRITEABLE BEFORE REPLACE/INSERTING !!!!!
                fopen.close()
                #if '44' in mutated_file_name or '45' in mutated_file_name:
                #    print 'os.path.exists(%s) = %d' % (mutated_file_name, os.path.exists(mutated_file_name))
                yield (offset, value['value'], value['type'], mutated_file_name)
                #except:
                #    raise Exception('[*] unable to open tmp file for mutation! %s '%mutated_file_name)

    def createWriteable(self, new_bytes):       ### XXX <----- IS THIS CHANGING ALL NUMBERS IN THE FILE TO CHARS? AND NOT JUST THE PAYLOAD???????
        for offset, value in enumerate(new_bytes):
            if str.isdigit(str(value)):
                new_bytes[offset] = chr(value)
