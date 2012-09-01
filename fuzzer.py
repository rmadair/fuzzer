from sys import exit, argv
from sys import stdout
from Mutator import Mutator
from Executor import executor
from time import ctime, time
from multiprocessing import Pool, Process, Pipe
from subprocess import Popen
import threading
import logging
import gc

# todo
#
# - make the to_run string (and the way the user defines where the mutated file goes in the command line) more generic
#   - fill in with a regex or something
#
# - allow a max time for a process to run
#
# - use the arg parse library
#
# - support multiple processes

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

    # parse command line args
    cmd_line        = argv[1]
    original_file   = argv[2]
    temp_directory  = argv[3]
    mutation_type   = argv[4]
    max_processes   = argv[5]
    logfile_name    = argv[6]
    save_directory  = argv[7]

    # typecast, create the worker pool
    max_processes   = int(max_processes)
    pool            = Pool(max_processes, maxtasksperchild=50)
    
    # log basic starting information
    logging.basicConfig(filename=logfile_name, level=logging.INFO)
    logging.info("Starting Fuzzer")
    logging.info("%s" % ctime())
    logging.info('cmd_line        = %s' % cmd_line)
    logging.info('original_file   = %s' % original_file)
    logging.info('temp_director   = %s' % temp_directory)
    logging.info('mutation_type   = %s' % mutation_type)
    logging.info('max_processes   = %d' % max_processes)
    logging.info('logfile_name    = %s' % logfile_name)
    logging.info('save_directory  = %s' % save_directory)

    # create the mutator, and log the possible values it will produce
    mutator = Mutator(original_file, temp_directory, mutation_type)    
    logging.info('total mutations = %d' % mutator.total_mutations)
    logging.info('possible mutation list :')
    for offset, mutation in enumerate(mutator.getValues()):
        logging.info('[%02d] : %s'% (offset, repr(mutation)) )

    # figure out some relative percentages
    ten_percent = mutator.total_mutations / 10
    percent = 0

    # the main loop - yield each mutation, execute and log it
    start_time = time()
    for counter, (offset, value_index, value_type, new_file) in enumerate(mutator.createNext()):

        # just for sanity
        if counter % ten_percent == 0:
            print '%02d%% - %s' % (percent, ctime())
            percent += 10

        torun = '%s %s' % (cmd_line, new_file)
        logger=logging.getLogger('Executor-%d'%counter)
        # awesome, but creates the files up front :( - pool.apply_async(executor, (torun,offset,value_index,new_file,counter,save_directory,0), callback=output_logging_callback)#logger))
        res = pool.apply(executor, (torun,offset,value_index,new_file,counter,save_directory))
        logging.info(res)

    # clean up and wait
    pool.close()
    pool.join()
    logging.info("test finished")
    end_time = time() - start_time
    print 'total time =', end_time
