from winappdbg import Debug, EventHandler, EventSift
from sys import exit, argv
from shutil import copy
import threading
import logging
import struct
import os
import glob


#### XXXXXX if wanting to do 64 bit and 32, just take out all 0x%08x and replace with a global define
####        ADDR_STRING or something like that...

# globals
#global debug
#global mutator ####
global logfile_name
#global mutation_generator
global save_directory

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
            for value in self.value_generator.values:
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
        

class MyEventHandler (EventHandler):
    global logfile_name

    def __init__(self):
        self.regs_of_interest = ['Esp', 'Ebp', 'Eip', 'Eax', 'Ebx', 'Ecx', 'Edx', 'Edi', 'Esi']
        self._EventHandler__apiHooks = None
        self.output = '' # where data to be logged will go
        
    def handleEvent(self, s, event):
        thread  = event.get_thread()
        context = thread.get_context()
        proc    = thread.get_process()

        # print given string
        self.output += '[*] Handling Event : %s at %s\n' % (s, proc.get_label_at_address(context['Eip']))

        self.output += '[*] Image Base : 0x%08x\n' % proc.get_image_base()

        # print registers
        self.print_registers(context)

        # print disassembly
        self.print_disassembly(thread)

        # print stack info
        self.print_stackdump(thread, context['Esp'])
        self.print_backtrack(thread)

        #print '[*] Peek Pointers in Registers'
        #print thread.peek_pointers_in_registers()

        self.output += '[*] Copying file to safe directory\n'
        # XXXXXXXX USE A REGEX TO PULL OUT THE FILE NAME CLEANLY!!!
        command_line = event.get_thread().get_process().get_command_line()
        fname = command_line.split()
        fname = ' '.join(fname[-3:])
        print 'copy(%s, %s)' % (fname, save_directory)
        print r'glob.glob(C:\DocumentsandSettings\Administrator\Desktop\fuzzing\fuzzer\tmp\files\) = %s' % (glob.glob(r'C:\DocumentsandSettings\Administrator\Desktop\fuzzing\fuzzer\tmp\files\*'))
        copy(fname, save_directory)

        self.output += '[*] Killing process...\n'
        proc.kill()

    def print_registers(self, context):
        self.output += '[*] Registers :\n'
        #print context
        for reg_key in context.keys():
            if reg_key in self.regs_of_interest:
                self.output += '%-5s = 0x%08x\n' % (reg_key, context[reg_key])    # XXXXXX FIX FOR 64 BIT

    def print_stackdump(self, thread, esp):
        self.output += '[*] Stack Dump :\n'
        try:
            stack_dwords = thread.read_stack_dwords(24)
            for i in range(0,24,4):
                self.output += '0x%08x : 0x%08x 0x%08x 0x%08x 0x%08x\n' % (esp+i*4, stack_dwords[i],stack_dwords[i+1],stack_dwords[i+2],stack_dwords[i+3])
            #print '[*] Peek Pointers in Data'
            #print thread.peek_pointers_in_data(thread.read_stack_data())
        except:
            self.output += '- unable to get stack frame -\n'

    def print_backtrack(self, thread):
        self.output += '[*] Stack Backtrace :\n'
        try:
            backtrace   = thread.get_stack_trace_with_labels()
            self.output += '- Ret Addr, Frame Pointer Label\n'
            for tup in backtrace:
                self.output += '0x%08x, 0x%s\n' % (tup[0], tup[1])
        except:
           self.output += '- unable to get backtrace -\n'
        
    def print_disassembly(self, thread):
        self.output += '[*] Disassembly :\n'
        try:
            disassembly = thread.disassemble_around_pc()
            for line in disassembly:
                self.output += '0x%08x : %-2d %-20s | %s%s\n' % (line[0], line[1], line[3], line[2], '   <----- Eip' if thread.get_pc() == line[0] else '')
        except:
            self.output += '- unable to disassemble -\n'
        

    def access_violation(self, event):
        self.handleEvent("access_violation", event)

    def stack_overflow(self, event):
        self.handleEvent("stack_overflow", event)

    def illegal_instruction(self, event):
        self.handleEvent("illegal_instruction", event)

    def integer_divide_by_zero(self, event):
        self.handleEvent("int_divide_by_zero", event)

    def array_bounds_exceeded(self, event):
        self.handleEvent("array_bounds_exceeded", event)
        
    def exit_process(self, event):
        proc = event.get_thread().get_process()
        # XXXXXXXX USE A REGEX TO PULL OUT THE FILE NAME CLEANLY!!!
        command_line = event.get_thread().get_process().get_command_line()

        fname = command_line.split()
        fname = ' '.join(fname[-3:])
        self.output += 'unlink(%s)' % fname
        os.unlink(fname)


def usage():
    print 'Usage : %s [program_cmd_line] [original_file] [temp_directory] [mutation_type] [max_processes] [log_file][save_directory]' % argv[0]
    print ''
    print 'program_cmd_line   - The command line, with a %s for the filename, that will be used to launch the target app'
    print 'original_file      - The original file to be mutated'
    print 'temp_directory     - A temporary directory for files to be placed'
    print 'mutation_type      - "byte", "word" or "dword" mutations'
    print 'max_processes      - The maximum number of simultaneous processes'
    print 'log_file           - A destination file for logging'
    print 'save_directory     - A directory to files that cause crashes will be saved to'
    print ''
    exit(1)

def monitor_thread(cmd_line, offset, value, value_type, new_file, run_number):
    ''' Setup the debugger and the event handler. Execute the process, and after completion log the
        run-specific information, as well as check for any specific output generated by the event handler. '''
    
    handler = MyEventHandler()
    debug   = Debug(handler)
    process = debug.execl(cmd_line)
    debug.loop()
    output = '%s %d %s\n' % ('-'*10, run_number, '-'*10)
    output += 'Running : %s\n' % cmd_line
    output += 'run number = %d, offset = %d, value = %s, value_type = %s' % (run_number, offset, repr(value), value_type)   # XXXXXXX don't want value printed, just an enum/key representing which value was used

    # if any signals are handled, debug output will be non-empty
    if handler.output:
        output += 'handler.output = %s\n' % handler.output          #### HAVE THIS GENERATE A HIGHER LOG LEVEL
    logging.info(output)


if __name__ == "__main__":
    if len(argv) != 8:
        usage()

    # denote globals
    global save_directory

    cmd_line        = argv[1]
    original_file   = argv[2]
    temp_directory  = argv[3]
    mutation_type   = argv[4]
    max_processes   = argv[5]
    logfile_name    = argv[6]   ##### XXXXXX I WANT TO LOG THESE INITIAL VALUES
    save_directory  = argv[7]

    print 'cmd_line        = %s' % cmd_line
    print 'original_file   = %s' % original_file
    print 'temp_director   = %s' % temp_directory
    print 'mutation_type   = %s' % mutation_type
    print 'max_processes   = %s' % max_processes
    print 'logfile_name    = %s' % logfile_name
    print 'save_directory  = %s' % save_directory
    
    logging.basicConfig(filename=logfile_name, level=logging.INFO)
    logging.info("test starting")
    mutator = Mutator(original_file, temp_directory, mutation_type)    
    print 'total mutations = %d' % mutator.total_mutations

    counter = 1
    
    for (offset, value, value_type, new_file) in mutator.createNext():
        if counter==50:
            break
        torun = '%s %s' % (cmd_line, new_file)
        thread = threading.Thread(target=monitor_thread, args=(torun,offset,value,value_type,new_file,counter))
        thread.run()
        while thread.isAlive():
            continue
        counter += 1
    logging.info("test finished")
