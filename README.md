propconfig
==========

Keep properties and config files updated by merging results with a YAML style config file.

Usage:

    propconfig.py [ -file <config yaml file> | -validate | -diff | -help ]

    Default:
        update property files from 'custom_config.yml'
        and print the number of changes made

    Optional settings:
        -f | --file <file>   : read configs from a specific yaml file
        -v | --validate      : checks if custom configs are in place
                         exit code is 0 if configs already set
        -d | --diff          : don't update the configs, just print the differences
        -s | --silent        : don't display the number of changes updated.
                         Warnings and errors will still be displayed
        -h | --help          : this message

Config File formatting:

    /full/path/to/config/file/1 :
        changeThisValue : to_this
        if.this.is.not.found :  It Will Be Appended to the Config
    
    # A double '!!' will comment out a Variable if it exists
    /full/path/to/file2 :
        toCommentOut :  !!
        
