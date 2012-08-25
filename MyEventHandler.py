from winappdbg import EventHandler, EventSift
from shutil import copy
from os import unlink
import glob

class MyEventHandler (EventHandler):
    ''' Override the default event handler to catch any signals we are interested in. At the same
        time log any output locally to self.output so the monitor can aggregate output. '''

    def __init__(self, filename, save_directory):
        self.filename           = filename
        self.save_directory     = save_directory
        self.output             = '' # where data to be logged will go
        self.regs_of_interest   = ['Esp', 'Ebp', 'Eip', 'Eax', 'Ebx', 'Ecx', 'Edx', 'Edi', 'Esi']
        self._EventHandler__apiHooks = None	# XXXXXXXXX would calling super fix this weird thing ??????

    def getOutput(self):
        ''' simple get method to return self.output '''
        return self.output
        
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
        print 'copy(%s, %s)' % (self.filename, self.save_directory)
        copy(self.filename, self.save_directory)

        self.output += '[*] Killing process...\n'
        proc.kill()

    def print_registers(self, context):
        ''' print the registers. REG = value. one per line '''

        self.output += '[*] Registers :\n'
        for reg_key in context.keys():
            if reg_key in self.regs_of_interest:
                self.output += '%-5s = 0x%08x\n' % (reg_key, context[reg_key])    # XXXXXX FIX FOR 64 BIT

    def print_stackdump(self, thread, esp):
        ''' show the next few dwords on the stack '''

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
        ''' print a backtrace '''

        self.output += '[*] Stack Backtrace :\n'
        try:
            backtrace   = thread.get_stack_trace_with_labels()
            self.output += '- Ret Addr, Frame Pointer Label\n'
            for tup in backtrace:
                self.output += '0x%08x, 0x%s\n' % (tup[0], tup[1])
        except:
           self.output += '- unable to get backtrace -\n'
        
    def print_disassembly(self, thread):
        ''' print the disassembly around EIP '''

        self.output += '[*] Disassembly :\n'
        try:
            disassembly = thread.disassemble_around_pc()
            for line in disassembly:
                self.output += '0x%08x : %-2d %-20s | %s%s\n' % (line[0], line[1], line[3], line[2], '   <----- Eip' if thread.get_pc() == line[0] else '')
        except:
            self.output += '- unable to disassemble -\n'
        

    # for all of these cases, we call handleEvent to do all the work
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
        ''' on exit, we remove the mutated file being tested. if it caused any 
            signals of interest the handleEvent function will save it. '''
        unlink(self.filename)
