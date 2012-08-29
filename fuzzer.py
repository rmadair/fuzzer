from sys import exit, argv
from Mutator import Mutator
from Executor import executor
from time import ctime
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

    
    logging.basicConfig(filename=logfile_name, level=logging.INFO)
    logging.info("Starting Fuzzer")
    logging.info("%s" % ctime())
    logging.info('cmd_line        = %s' % cmd_line)
    logging.info('original_file   = %s' % original_file)
    logging.info('temp_director   = %s' % temp_directory)
    logging.info('mutation_type   = %s' % mutation_type)
    logging.info('max_processes   = %s' % max_processes)
    logging.info('logfile_name    = %s' % logfile_name)
    logging.info('save_directory  = %s' % save_directory)

    mutator = Mutator(original_file, temp_directory, mutation_type)    
    logging.info('total mutations = %d' % mutator.total_mutations)
    logging.info('possible mutation list :')
    for offset, mutation in enumerate(mutator.getValues()):
        logging.info('[%02d] : %s'% (offset, repr(mutation)) )

    counter = 0
    for (offset, value_index, value_type, new_file) in mutator.createNext():
        if counter==50:
            break
        torun = '%s %s' % (cmd_line, new_file)
        logger=logging.getLogger('Executor-%d'%counter)
        thread = threading.Thread(target=executor, args=(torun,offset,value_index,value_type,new_file,counter,save_directory,logger))
        thread.run()
        while thread.isAlive():
            continue
        counter += 1
    logging.info("test finished")
