import struct
from sys import exit
from os.path import splitext, join

import mutations

class Mutator():

    def __init__(self, original_file, mutation_types, original_file_name, directory):
        self.original_file  = original_file		# original contents of file
        self.mutation_types = mutation_types	# list of possible mutations
        self.directory  = directory
        self.original_file_name = original_file_name
        self.original_file_base = splitext(self.original_file_name) [0]
        self.original_file_ext  = splitext(self.original_file_name) [1]

    def createMutatedFileName(self, offset, mutation_index):
        ''' create a file name that represents the current mutation, return it '''
        fname = '%s-%d-%d%s' % (self.original_file_base, offset, mutation_index, self.original_file_ext)
        return fname

    def createMutatedFile(self, offset, mutation_index):
        ''' mutate the contents of the original file, at offset, with mutation at 
            mutation_index, creating a new file. return the new file name '''

        new_bytes = list(self.original_file[:])
        mutation  = self.mutation_types[mutation_index]

        if mutation['type'] == 'replace':
            new_bytes[offset:offset+mutation['size']] = mutation['value']                 # if 'replace', then just substitute/replace the desired bytes
        elif mutation['type'] == 'insert':
            new_bytes = new_bytes[:offset] + list(mutation['value']) + new_bytes[offset:]    # if 'insert', stick them in, shifting the rest of the bytes down
        else:
             raise Exception('[*] UNKNOWN mutation[\'type\'], %s' % mutation['type'])

        # create the new file name, then it's full path
        mutated_file_name = self.createMutatedFileName(offset, mutation_index)
        mutated_file_name = join(self.directory, mutated_file_name)

        # write the file
        try:
            with open(mutated_file_name, 'wb') as fopen:
                fopen.write( ''.join(new_bytes) ) 
        except Exception as e:
            raise Exception('[*] unable to open tmp file for mutation! Error : %s' % e)

        return mutated_file_name

class MutationGenerator():

    def __init__(self, value_type, strings=False):
        self.generateValues(value_type, strings)

    def generateValues(self, value_type, strings):
        values = []
        if value_type == 'byte':
            values.extend(mutations.values_8bit)
        elif value_type == 'word':
            values.extend(mutations.values_16bit)
        elif value_type == 'dword':
            values.extend(mutations.values_32bit)
        else:
            raise Exception('unknown value type passed to generateValues(...), %s' % value_type)

        if strings:
            values.extend(mutations.values_strings)

        # turn them into writeable bytes
        self.value_to_bytes(values, vtype=value_type)
        self.createWriteable(values)
        self.createStrings(values)
        self.values = values

    def createStrings(self, values):
        for value_dict in values:
            value_dict['value'] = ''.join(value_dict['value'])

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
