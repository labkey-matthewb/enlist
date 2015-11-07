#! /usr/bin/python

import sys
import enlist_main

argv = []
argv.extend(sys.argv)
argv.append("enlist")

enlist_main.main(argv)