#!/usr/bin/env python
import sys, os

def usage ():
    print "usage: %s <filename> <hex begin> (optional: hex end)" % \
          os.path.basename(sys.argv[0])
    sys.exit (1)

if __name__ == "__main__":
  if len(sys.argv) < 3:
      usage ()
  if len(sys.argv) > 3:
      endMark = ":" + sys.argv[3]
  else:
      endMark = "}"
  
  outputFile = sys.stdout
  inputFile = open (sys.argv[1])
  beginVal = ":" + sys.argv[2]
  
  line = inputFile.readline ()
  while line:
      if line[:len(beginVal)] == beginVal:
          break;
      line = inputFile.readline ()
  
  outputFile.write (line)
  
  line = inputFile.readline ()
  while line:
      if line[:len(endMark)] == endMark:
          break
      outputFile.write (line)
      line = inputFile.readline ()
  
  inputFile.close ()
  outputFile.close ()
