#!/usr/bin/env python
__author__ = 'esales'

YAML_CONF = "custom_config.yml"


INFO="""
    propconfig
        Update Property files from a custom merge file.
"""

USAGE="""
    propconfig.py [ -file <file> | -validate | -diff | -help ]

    Default:
        update property files from '%s'
        and print the number of changes made

    Optional settings:
        -f | --file <file>   : use config from a specific yaml file
        -v | --validate      : checks if custom configs are in place
                         exit code is 0 if configs already set
        -d | --diff          : don't update the configs, just print the differences
        -s | --silent        : don't display the number of changes updated.
                         Warnings and errors will still be displayed
        -h | --help          : this message
""" % YAML_CONF


import fileinput
import sys, os

SILENT = False

def usage():
    print INFO
    print USAGE


def _ProcessArgs(cliArgs):
    global YAML_CONF
    global SILENT
    RetCmd="update"

    i = 1
    while i < len(cliArgs):

        if cliArgs[i] in ('-f','--file', '-file'):
            try:
                YAML_CONF = cliArgs[i+1]
                i = i + 1
            except IndexError:
                print "Error: file not specified with '-file' flag."
                sys.exit(1)
        elif cliArgs[i] in ('-validate','--validate','validate','-v'):
            RetCmd = "validate"
        elif cliArgs[i] in ('-diff', '--diff', 'diff','-d'):
            RetCmd = "diff"
        elif cliArgs[i] in ('-silent','silent','--silent','-s'):
            SILENT = True
        elif cliArgs[i] in ('-h','-?','help','--help','-help'):
            usage()
            sys.exit(1)
        else:
            print "Error: unknown arg '%s'" % (cliArgs[i])
            usage()
            sys.exit(2)
        i = i + 1

    return RetCmd


def doIprint(msg):
    """Print my message if SILENT is false"""
    if not SILENT:
        print msg

def ErrorMsg(msg):
    """
    Exit with error message
    """
    print msg
    sys.exit(2)


def loadConfig(yamlFile):
    """
    Load the yaml config file in memory
    """
    ## we're not really using the yaml module - because RHEL5 python sucks
    yamlRet = {}

    if os.path.isfile(yamlFile):
        # If the file exists lets try to open it #
        try:
            f = open(yamlFile, 'r')
            fhead = ''
            key = ''
            value = ''
            for line in f:
                # process lines that are not empty or comment lines #
                if not line.lstrip().startswith('#') and line not in ('\n'):
                    # checking syntax #
                    if not fhead:
                        if line.startswith(' ') or not line.rstrip().endswith(':'):
                            print "line: %s" % (line)
                            ErrorMsg("Error: config file %s syntax error" % (yamlFile))
                        else:
                            # Initialize Header Key #
                            fhead = line.split(':')[0].strip()
                            fdict = {}
                    else:
                        # check if filename or key/value pair
                        #  if filename, then assign fhead : fdict to yamlRet
                        #    and set new fhead and reset fdict
                        if not line.startswith(' '):
                            # expect a filename header line
                            if not line.rstrip().endswith(':'):
                                print "line: %s" % (line)
                                ErrorMsg("Error: expecting a ':' at the end of the filename key line")
                            else:
                                if fdict:
                                    yamlRet[fhead] = fdict
                                # reset fhead and fdict
                                fhead = line.split(':')[0].strip()
                                fdict = {}
                        else:
                            # expect a key/value pair
                            if ':' not in line:
                                ErrorMsg("Error: expecting a ':' to define a 'key: value'")
                            else:
                                key = str(line.split(':')[0]).strip()
                                value = str(':'.join(line.split(':')[1:])).strip()
                                # It's okay if Value is ''
                                if key:
                                    fdict[key] = value
                                else:
                                    ErrorMsg("Error: bad 'key: value' pair syntax.")
            f.close()
            # flush the key/value pairs #
            if fdict:
                yamlRet[fhead] = fdict
        except IOError:
            print "Error: Cannot load yaml config file %s" % (yamlFile)
            sys.exit(2)

    return yamlRet


def verifyChanges(Configs):
    """Returns a Dict of files and changes to be made"""
    RetDict = {}
    # Variables to comment out 
    CommList = []

    for f in Configs.keys():
        # Check that the file exists before we process it #
        if not os.path.isfile(f):
            print "[Warning]: config file not found.  Ignoring settings."
            print "  %s" % (f)
        else:
            # Dict of variables and configs for this file
            pConfigs = Configs[f]

            for line in open(f):
                l = line.split('#')[0].strip()
                if l and ('=') in l:
                    lvar = str(l.split('=')[0].strip())
                    lval = str(l.split('=')[1].strip())

                    if lvar in pConfigs.keys():
                        if lval == pConfigs[lvar]:
                            # Config is already set, remove it from pConfigs
                            del pConfigs[lvar]
                        elif pConfigs[lvar] == '!!':
                            CommList.append(lvar)
                            
            # remove any left over commented out pConfigs
            for pCon in pConfigs.keys():
                if pConfigs[pCon] == '!!' and pCon not in CommList:
                    del pConfigs[pCon]

            if pConfigs:
                RetDict[f] = pConfigs
    
    return RetDict


def showUpdates(File, Configs):
    """ Display the update configs for File """
    print "file:  %s" % (File)
    for v in Configs.keys():
        if Configs[v] == '!!':
            print "    %s => (Comment Out)" % (v)
        else:
            print "    %s => %s" % (v, Configs[v])

def makeUpdates(File, Configs):
    """ Make the config updates to File """
    updateCnt = 0
    newVarCnt = 0
    varsToUpdate = Configs.keys()

    for line in fileinput.input(File, inplace = 1):
        # process lines that look like config settings #
        if not line.lstrip(' ').startswith('#') and '=' in line:
            for v in varsToUpdate:
                lvar = str(line.split('=')[0].strip())
                lval = str(line.split('=')[1].strip())
                if lvar == v:
                    # We comment out the existing line and use the new setting
                    commLine = "# " + line
                    if Configs[v] == '!!': 
                        line = commLine 
                    else:
                        sys.stdout.write(commLine)
                        line = "%s=%s\n" % (v,Configs[v])
                    updateCnt = updateCnt + 1
                    varsToUpdate.remove(v)
        sys.stdout.write(line)

    # Append any settings that's left over #
    if varsToUpdate:
        newVarCnt = len(varsToUpdate)
        try:
            f = open(File, 'a')
            for x in varsToUpdate:
                appvar = x
                appval = Configs[x]
                if appval != '!!':
                    # We don't need to append any commented out variables
                    f.write("%s=%s\n" % (appvar,appval))
            f.close()
        except IOError:
            ErrorMsg("Error: cannot append to '%s'!" % (File))

    doIprint("file =>  %s " % (File))
    doIprint("    keys updated: %s\n    keys added: %s" % (updateCnt, newVarCnt))



### main ##
if __name__ == "__main__":
    FoundChanges = 0
    FoundDiffs = {}
    UpdateConfigs = True

    mainCmd = _ProcessArgs(sys.argv)

    #read yaml config in memory
    CustConfigs = loadConfig(YAML_CONF)
    ChangesToMake = verifyChanges(CustConfigs)

    if mainCmd == 'validate':
        if ChangesToMake:
            doIprint("Found (%s) files that need to be updated." % (len(ChangesToMake.keys())))
            exitcode = 1
        else:
            doIprint("All files are updated.")
            exitcode = 0
        sys.exit(exitcode)


    if ChangesToMake:
        for f in ChangesToMake.keys():
            if mainCmd == 'diff':
                showUpdates(f,ChangesToMake[f])
            if mainCmd == 'update':
                makeUpdates(f,ChangesToMake[f])
    else:
        doIprint("All files are already up to date.")




