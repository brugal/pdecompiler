#!/usr/bin/env python
import sys, os, string
from LineData import LineData
from UserList import UserList

TRUE = 1
FALSE = 0

def usage ():
    print "%s <filename>" % os.path.basename(sys.argv[0])
    sys.exit (1)

def is_hex_number (text):
    if len(text) >= 2:
        if text[:len("0x")] == "0x"  or  text[:len("0x")] == "0X":
            text = text[2:]
    for c in text:
        if c not in string.hexdigits:
            return FALSE
    return TRUE

class I386Stack (UserList):
    """A stack (push,pop methods) which 'grows towards lower memory'"""
    def push (self, x):
        if x in ("esp", "esi", "edi", "ebp", "eax", "ebx", "ecx", "edx")  or \
           is_hex_number(x):
            for i in range(3):
                self.insert (0, "<")
            self.insert (0, x)
        else:
            raise Exception, "FIXME: don't know how to 'push' %s" % x
    def pop (self):
        val = self[0]
        #FIXME doesn't work??? self = self[4:]
        for i in range(4):
            self.remove (self[0])
        return val
    def add (self, x):
        if x < 0:
            self.sub (-x)
        else:
            #FIXME why doesn't the following work?  ->  self = self[x:]
            for i in range(x):
                self.remove (self[0])
    def sub (self, x):
        if x < 0:
            self.add (-x)
        else:
            for i in range(x):
                self.insert (0, None)

def test ():
    return I386Stack ()

if __name__ == "__main__":
  if len(sys.argv) != 2:
      usage ()
  f = open (sys.argv[1])
  lines = f.readlines ()
  f.close ()

  ldata = []
  for line in lines:
      ldata.append (LineData(line))

  """
  for d in ldata:
      if d.isAssembler:
          print d.instruction
  """

  asmStack = I386Stack ()
  #try:
  for d in ldata:
      if not d.isAssembler:
          continue
      if len(d.args) == 0:
          continue
      if len(d.args) == 2  and  d.args[0] != "esp":
          continue
      
      if d.instruction == "push":
          asmStack.push (d.args[0])
      elif d.instruction == "pop":
          asmStack.pop ()
      elif d.instruction == "add":
          asmStack.add (string.atol(d.args[1], 16))
      elif d.instruction == "sub":
          asmStack.sub (string.atol(d.args[1], 16))
      else:
          continue
      print d.full_text,
      print asmStack
  #except Exception, message:
  #     print message
  #     print d.full_text
  #     sys.exit (1)
  #print asmStack
