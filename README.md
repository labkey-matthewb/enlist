# enlist

This is a tool to help create LabKey enlistments in known/correct configurations.
  
To create a completely new release15.3 enlistment, assuming ~/enlist/bin is on your path.

```
$ mkdir release15.3

$ cd release15.3

$ enlist.py ~/enlist/release15_3.config

$ check.py -v
```

To change to the modules15.3 branch
```
$ enlist.py ~/enlist/modules15_3.config

$ check.py -v
```

# mr
Enlist should interoperate with with **mr**. There is a copy in the bin/. see here for documentation: https://github.com/joeyh/myrepos


# todos and ideas
* bash and windows shell wrappers
* create config from existing enlistments
* merge option for enlist (don't overwrite local updates to .mrconfig)
* manage active modules in intellij .ipr
* manage database connections
