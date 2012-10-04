#!/usr/bin/env python
import sys, os
from Parser import Parser

TRUE = 1
FALSE = 0

def usage ():
    print "usage: %s [options] <filename>" % os.path.basename(sys.argv[0])
    print "  options:"
    print "-d  debug"
    sys.exit (1)

if __name__ == "__main__":
  # parse options
  debug = FALSE
  for a in sys.argv:
      if a == "-d":
          debug = TRUE
          sys.argv.remove (a)
          break
  if len(sys.argv) != 2:
      usage ()
  inFile = open (sys.argv[1])
  p = Parser (inFile=inFile, outFile=sys.stdout, debug=debug)
  p.run ()
  inFile.close ()
  
  
  
