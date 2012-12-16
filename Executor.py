from pydbg import *
from pydbg.defines import *
from time import time, sleep
import utils

class Executor():
    def __init__(self, timeout=5):
        self.timeout   = timeout
        self.output    = None

    def execute(self, command, args):
        self.output = None
        dbg = pydbg()
        dbg.set_callback(EXCEPTION_ACCESS_VIOLATION, self.handle_av)
        dbg.set_callback(0xC000001D, self.handle_av) # illegal instruction
        dbg.set_callback(USER_CALLBACK_DEBUG_EVENT, self.timeout_callback)
        dbg.load(command, command_line=args)
        dbg.start_time = time()
        dbg.run()

        return self.output

    def timeout_callback(self, dbg):
        if time() - dbg.start_time > self.timeout:
            dbg.terminate_process()
            return DBG_CONTINUE

    def handle_av(self, dbg):
        crash_bin = utils.crash_binning.crash_binning()
        crash_bin.record_crash(dbg)
        self.output = crash_bin.crash_synopsis()

        dbg.terminate_process()
        return DBG_EXCEPTION_NOT_HANDLED
