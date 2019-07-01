import logging
import platform
import subprocess
import sys
from optparse import OptionParser

ROUSER = "ro"
ROPASS = "user"

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

def get_nodetool_command(options, *args):
    cmd = [options.nodetool]
    cmd.extend(["-u", options.username, "-pwf", options.pass_file])
    if(options.username and options.password):
        cmd.extend(["-u", options.username, "-pw", options.password])
    cmd.extend(args)
    return cmd

def get_tokens(options):
    tokens = []
    cmd = get_nodetool_command(options, "describering" , options.keyspace)
    success, _, stdout, stderr = run_command(*cmd)
    
    for line in stdout.split('\n'):
        if line.startswith("\tTokenRange("):
            l = line.split()
            tokens.append((l[0].replace("TokenRange(start_token:","")[:-1],l[1].replace("end_token:","")[:-1]))
    return tokens

def main():

    parser = OptionParser()
    parser.add_option("-k", "--keyspace", dest="keyspace", metavar="KEYSPACE",
                      help="Keyspace to repair (REQUIRED)")

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

    parser.add_option("-s", "--st", dest="st", default=None,
                      metavar="ST", help="Start token; if [all] is specified repair all token one by one")

    parser.add_option("-F", "--passfile", dest="pass_file", default="/etc/cassandra/jmxremote.password",
                      metavar="PASSWORD", help="Password to use for nodetool/cqlsh commands")

    parser.add_option("-n", "--nodetool", dest="nodetool", default="nodetool",
                      metavar="NODETOOL", help="Path to nodetool [default: %default]")
    parser.add_option("-c", "--columnfamily", dest="columnfamily", default=[],
                      action="append", metavar="COLUMNFAMILY",
                      help="ColumnFamily to repair, can appear multiple times")
    parser.add_option("--py", dest="python", default="python",
                      metavar="python", help="Path to python [default: %default]")

    parser.add_option("--syslog", dest="syslog", metavar="FACILITY",
                      help="Send log messages to the syslog")

    parser.add_option("--logfile", dest="logfile", metavar="FILENAME", default=None,
                      help="Send log messages to a file")

    parser.add_option("-d", "--debug", dest="debug", action='store_true',
                      default=False, help="Debugging output")

    parser.add_option("-v", "--verbose", dest="verbose", action='store_true',
                      default=False, help="Verbose output")

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
    tokens = get_tokens(options)
    perc = len(tokens) / 100.00
    print(perc)
    print (options.st)
    for token in tokens:
        if token[0] == options.st:
         print("Percent complate: " , (tokens.index(token)+1)/perc)

if __name__ == "__main__":
    main()