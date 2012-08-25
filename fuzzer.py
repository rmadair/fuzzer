from sys import exit, argv
from Mutator import Mutator
from Executor import executor
import threading
import logging

#### XXXXXX if wanting to do 64 bit and 32, just take out all 0x%08x and replace with a global define
####        ADDR_STRING or something like that...

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
        logger=logging.getLogger('Executor-%d'%counter)
        thread = threading.Thread(target=executor, args=(torun,offset,value,value_type,new_file,counter,save_directory,logger))
        thread.run()
        while thread.isAlive():
            continue
        counter += 1
    logging.info("test finished")
