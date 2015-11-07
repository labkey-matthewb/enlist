#! /usr/bin/python

import sys
import enlist_main

argv = []
argv.extend(sys.argv)
argv.append("check")

enlist_main.main(argv)