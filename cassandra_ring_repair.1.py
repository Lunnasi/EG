"""
Repair options:
  * repair -full $ks  - for one keyspace (just use parrameter -k [keyspace_name])
     - python cassandra_ring_repair.1.py -k rbow_journal
  * repair -full $ks $cf - enumerate_keyspaces(options)
     - python cassandra_ring_repair.1.py -k rbow_journal -c messages
  * repair -full $ks $st [all] || [token to start from]
     - python cassandra_ring_repair.1.py -k preprod_replicator -s all
     - python cassandra_ring_repair.1.py -k preprod_replicator -s -7637099937400767109
  * repair -full $ks $st $w [int] 
     - python cassandra_ring_repair.1.py -k preprod_replicator -s all -w 8
     - python cassandra_ring_repair.1.py -k preprod_replicator -s 3219027497221808786 -w 4
  * restore repair if it fails for specific start token and will continue until end of token list
"""
import os
import logging
import logging.handlers
import operator
import platform
import sys
import multiprocessing as mp
import subprocess
import datetime
from multiprocessing.managers import BaseManager
from optparse import OptionParser, OptionGroup

ROUSER= "ro"
ROPASS= "xxxxx"
LOG_DIR= "/home/sseikins/logs"
logfile= LOG_DIR + 'cassandra-ring-repair-'+ datetime.datetime.now().strftime("%Y-%m-%d") + '.log'
start_token = "all"
log_level = "debug"
excluded_keyspaces = "rbow_journal,preprod_replicator"
scr_dir = "/home/sseikins/"
workers_pool = "8"

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def cass_status(options):
    cmd = get_nodetool_command(options , "status")
    success, _, stdout, stderr = run_command(*cmd)
    for line in stdout.split("\n"):
        print(line)

def setup_logging(option_group):
    """Sets up logging in a syslog format by log level
    :param option_group: options as returned by the OptionParser
    """
    stderr_log_format = "%(levelname) -10s %(asctime)s %(funcName) -20s line:%(lineno) -5d: %(message)s"
    file_log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logger = logging.getLogger()
    if option_group.debug:
        logger.setLevel(level=logging.DEBUG)
    elif option_group.verbose:
        logger.setLevel(level=logging.INFO)
    elif option_group.verbose:
        logger.setLevel(level=logging.WARNING)

    handlers = []
    if option_group.syslog:
        handlers.append(logging.handlers.SysLogHandler(facility=option_group.syslog))
        # Use standard format here because timestamp and level will be added by syslogd.
    if option_group.logfile:
        handlers.append(logging.FileHandler(option_group.logfile))
        handlers[0].setFormatter(logging.Formatter(file_log_format))
    if not handlers:
        handlers.append(logging.StreamHandler())
        handlers[0].setFormatter(logging.Formatter(stderr_log_format))
    for handler in handlers:
        logger.addHandler(handler)
    return

def f_second_val(val):
    return val[1]

def f_third_val(val):
    return val[2]

def keyspaces_sorted_by_size(options):
    """
    Return keyspaces , sum of collumn families sizes(Space used (total)) ordered by size desc
    """
    lst_sizes = enumerate_keyspaces(options)
    lst_keyspaces = get_keyspaces(options)
    keyspaces = []
    for x in lst_keyspaces:
        ksize = 0
        for y in lst_sizes:
                if x == y[0]:
                    ksize =+ y[2]
        keyspaces.append((x,ksize))
    keyspaces.sort(key=f_second_val)
    return keyspaces

def enumerate_keyspaces(options):
    # Build a list of keyspace/column families/size
    # sort list by cf size desc
    logging.info('running nodetool cfstats')
    lst_keyspace = get_keyspaces(options)
    keyspaces = []
    # Remove all excluded keyspaces from list
    if options.exclude:
        for y in options.exclude.split(","):
            for x in lst_keyspace:
                if x == y:
                    lst_keyspace.remove(x)

    for x in lst_keyspace:
        cmd = get_nodetool_command(options, "cfstats", x)
        success, _, stdout, stderr = run_command(*cmd)
        if not success:
            raise Exception("Died in enumerate_keyspaces because: " + stderr)
        logging.debug('cfstats retrieved, parsing output to retrieve keyspaces')
    
        for line in stdout.split("\n"):
            if line.startswith('Keyspace : '):
                keyspace = line.replace("Keyspace : ", "")
            elif line.startswith("\t\tTable: "):
                table = line.replace("\t\tTable: ", "")
            elif line.startswith("\t\tSpace used (total): "):
                size = line.replace("\t\tSpace used (total): ","")
                keyspaces.append((keyspace,table,int(size)))
    logging.info('Found {0} cf'.format(len(keyspaces)))
    logging.debug(keyspaces)
    keyspaces.sort(key=f_third_val)
    return keyspaces

def get_nodetool_command(options, *args):
    cmd = [options.nodetool]
    cmd.extend(["-u", options.username, "-pwf", options.pass_file])
    if(options.username and options.password):
        cmd.extend(["-u", options.username, "-pw", options.password])
    cmd.extend(args)
    return cmd

def get_cqlsh_command(options, *args):
    cmd = [options.cqlsh]
    cmd.extend(["-u", options.rouser, "-p", options.ropass, options.host])
    if(options.username and options.password):
        cmd.extend(["-u", options.username, "-pw", options.password])
    cmd.extend(args)
    return cmd

def run_command(*command):
    """Execute a shell command and return the output
    :param command: the command to be run and all of the arguments
    :returns: success_boolean, command_string, stdout, stderr
    """
    cmd = " ".join(map(str, command))
    logging.debug("run_command: " + cmd)
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = proc.communicate()
    return proc.returncode == 0, cmd, stdout, stderr

def get_keyspaces(options):
    cmd = get_cqlsh_command(options , "-e \"SELECT keyspace_name FROM system_schema.keyspaces;\"")
    success, _, stdout, stderr = run_command(*cmd)
    keyspaces = []
    i = 0
    for line in stdout.split("\n"):
        i += 1
        if i>3:
            if not line:
                break
            else:
                keyspaces.append(line.replace(" ",""))
    return keyspaces

def get_tokens(options):
    tokens = []
    cmd = get_nodetool_command(options, "describering" , options.keyspace)
    success, _, stdout, stderr = run_command(*cmd)
    
    for line in stdout.split('\n'):
        if line.startswith("\tTokenRange("):
            l = line.split()
            tokens.append((l[0].replace("TokenRange(start_token:","")[:-1],l[1].replace("end_token:","")[:-1]))
    return tokens

def _repair_cmd(options):
    cmd = get_nodetool_command(options, "repair")
    if not options.inc:
        cmd.append("--full")
    if options.keyspace:
        cmd.append(options.keyspace)
        if options.columnfamily:
            if options.columnfamily != "all":
                keyspaces = enumerate_keyspaces(options)
                for x in keyspaces:
                    for y in options.columnfamily:
                        if x[0] == options.keyspace and x[1] == options.columnfamily[0]:
                            cmd.append(x[1])
    return cmd

#return list of all keyspaces with columnspaces
def repair_keyspaces(options):
    lst_cmd = []
    keyspaces = enumerate_keyspaces(options)
    for keyspace in keyspaces:
        cmd = get_nodetool_command(options, "repair")
        if not options.inc:
            cmd.append("--full")
        cmd.extend([keyspace[0], keyspace[1],  "-local"])
        lst_cmd.append(cmd)
    return lst_cmd

#return list of lst_cmd with st et for specific keyspace(as options)   
def st_repair(options):
    lst_cmd = []
    tokens = get_tokens(options)
    if options.st == "all":
        for line in tokens:
            cmd = _repair_cmd(options)
            cmd.extend(["-st ", line[0], "-et", line[1]])
            lst_cmd.append(cmd)  
        return lst_cmd
    else:
        t_len = len(tokens)
        i = 0
        for item in tokens:
            if tokens[i][0] == options.st:
                i += 1
                break
            i += 1
        while i < t_len:
            cmd = _repair_cmd(options)
            cmd.extend(["-st ", tokens[i][0], "-et", tokens[i][1]])
            lst_cmd.append(cmd)
            i += 1
        return lst_cmd

            #i = tokens.index(options.st)
            #print(tokens[i])

#miltiprocessing workers count depends on option. default is 2
def multi_repair(cmd, options):
    pool = mp.Pool(options.workers)
    results = [pool.apply_async(run_command,args=(command)) for command in cmd]
    output = [p.get() for p in results]
    return output

def repair(options):
    if options.st:
        cmd = st_repair(options)
        out = multi_repair(cmd,options)
        '''
        for command in cmd:
            success, _, stdout, stderr = run_command(*command)
            print(_)
        '''
        '''            
            proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, universal_newlines=True)
            success, _, stdout, stderr = run_command(*command)
            if not success:
                raise Exception("Died in repair because: " + stderr)
                logging.debug('Died in repair on: ' + command)
            else: 
                logging.info('Restore completed for {0} succesfully'.format(command[-5:]))
                logging.debug(stdout)
        '''
    elif options.keyspace:
        cmd = _repair_cmd(options)
        success, _, stdout, stderr = run_command(*cmd)
        wr_log(success,stderr,stdout,cmd)
    else:
        cmd = repair_keyspaces(options)
        for command in cmd:
            success, _, stdout, stderr = run_command(*command)
            wr_log(success,stderr,stdout,command)

def wr_log(success,stderr,stdout,command):
    if not success:
        raise Exception("Died in repair because: " + stderr)
        logging.debug('Died in repair on: ' + command)
    else: 
        logging.info('Restore completed for {0} succesfully'.format((command[-3] + " " + command[-2])))
        logging.debug(stdout)

def get_python(options,*args):
    cmd = [options.python]
    cmd.extend(args)
    return cmd

def daily_quest(options, *args):
    cmd = get_python(options, scr_dir+"cassandra_ring_repair.py", "--"+log_level,"--logfile", logfile ,"-e", excluded_keyspaces)
    success, _, stdout, stderr = run_command(*cmd)

def excluded_repair(options, *args):
    for keyspace in excluded_keyspaces.split(","):
        cmd = get_python(options, scr_dir+"cassandra_ring_repair.1.py", "--"+log_level, "--logfile", logfile , "-k" , keyspace, "-s all", "-w", workers_pool )
        print(cmd)
        success, _, stdout, stderr = run_command(*cmd)

def main():

    parser = OptionParser()
    parser.add_option("-k", "--keyspace", dest="keyspace", metavar="KEYSPACE",
                      help="Keyspace to repair (REQUIRED)")

    parser.add_option("-c", "--columnfamily", dest="columnfamily", default=[],
                      action="append", metavar="COLUMNFAMILY",
                      help="ColumnFamily to repair, can appear multiple times")

    parser.add_option("-H", "--host", dest="host", default=platform.node(),
                      metavar="HOST", help="Hostname to repair [default: %default]")

    parser.add_option("-P", "--port", dest="port", default=7199, type="int",
                      metavar="PORT", help="JMX port to use for nodetool commands [default: %default]")

    parser.add_option("-u", "--username", dest="username", default="controlRole",
                      metavar="USERNAME", help="Username to use for nodetool commands")

    parser.add_option("-r", "--rouser", dest="rouser", default=ROUSER,
                      metavar="ROUSER", help="ROUSER to use for cqlsh commands")

    parser.add_option("-R", "--ropass", dest="ropass", default=ROPASS,
                      metavar="ROPASS", help="ROPASS to use for cqlsh commands")          
    
    parser.add_option("-p", "--password", dest="password", default=None,
                      metavar="PASSWORD", help="Password to use for nodetool/cqlsh commands")

    parser.add_option("-F", "--passfile", dest="pass_file", default="/etc/cassandra/jmxremote.password",
                      metavar="PASSWORD", help="Password to use for nodetool/cqlsh commands")

    parser.add_option("-s", "--st", dest="st", default=None,
                      metavar="ST", help="Start token; if [all] is specified repair all token one by one")

    parser.add_option("-n", "--nodetool", dest="nodetool", default="nodetool",
                      metavar="NODETOOL", help="Path to nodetool [default: %default]")

    parser.add_option("--py", dest="python", default="python",
                      metavar="python", help="Path to python [default: %default]")
    
    parser.add_option("-C", "--cqlsh", dest="cqlsh", default="cqlsh",
                      metavar="CQLSH", help="Path to cqlsh [default: %default]")
    
    parser.add_option("-i", "--inc", dest="inc", default=False, action='store_true',
                      metavar="INC", help="Carry out an incremental repair  Bugged until 4.0")

    parser.add_option("-e", "--ex", dest="exclude", default=[],
                      metavar="EXC", help="Exclude keyspace(s)")

    parser.add_option("--syslog", dest="syslog", metavar="FACILITY",
                      help="Send log messages to the syslog")

    parser.add_option("--logfile", dest="logfile", metavar="FILENAME", default=None,
                      help="Send log messages to a file")

    parser.add_option("-d", "--debug", dest="debug", action='store_true',
                      default=False, help="Debugging output")

    parser.add_option("-v", "--verbose", dest="verbose", action='store_true',
                      default=False, help="Verbose output")

    parser.add_option("-w", "--workers", dest="workers", type="int",
                      default=2, help="Multiprocess workers. used for st repair")

    parser.add_option("--daily", dest="daily_sh", action='store_true',
                      default=False, help="Passing params from daily job")
    
    parser.add_option("--status", dest="status", action='store_true',
                      default=False, help="check cluster status")
    
    parser.add_option("--size", dest="sized", action='store_true',
                      default=False, help="check keyspaces size")
    
    parser.add_option("--excluded", dest="excluded", action='store_true',
                      default=False, help="RUnning repair on excluded keyspaces")

    (options, args) = parser.parse_args()

    setup_logging(options)

    if options.columnfamily and not options.keyspace: # keyspace is a *required* for columfamilies
        parser.print_help()
        logging.debug('Invalid configuration options')
        sys.exit(1)
   
    if args:                    # There are no positional parameters
        parser.print_help()
        logging.debug('Extra parameters')
        sys.exit(1)

    if options.daily_sh:
        daily_quest(options)
    elif options.excluded:
        excluded_repair(options)
    else: 
        repair(options)

#    excluded_repair(options)
    logging.debug("Test for excluded keyspaces")

    exit(0)


if __name__ == "__main__":
    main()
