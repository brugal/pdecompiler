import string
from LineData import LineData

TRUE = 1
FALSE = 0

class Parser:
 def __init__ (self, inFile, outFile, debug=FALSE):
     self.inFile = inFile
     self.outFile = outFile
     self.debug = debug
     self.instr_to_func = { \
         "add"   : self.handle_add,
         "and"   : self.handle_and,
         "cmp"   : self.handle_cmp_test,
         "dec"   : self.handle_dec,
         "DWORD" : self.handle_DWORD,
         "inc"   : self.handle_inc,
         "jmp"   : self.handle_jmp,
         "lea"   : self.handle_lea,
         "mov"   : self.handle_mov,
         "or"    : self.handle_or,
         "push"  : self.handle_default,
         "ret"   : self.handle_ret,
         "sub"   : self.handle_sub,
         "test"  : self.handle_cmp_test,
         "xor"   : self.handle_xor
     }
 def handle_default (self):
     outFile = self.outFile
     c = self.current
     outFile.write ("    ; %s" % c.instruction)
     if len(c.args) > 0:
         outFile.write (" %s" % string.join(c.args, ", "))
     if c.comments != None:
         outFile.write ("  // %s" % c.comments)
     if c.instruction in ("cmp", "test")  or  c.instruction[0] == "j":
         outFile.write ("  // %s" % c.address)
     outFile.write ("\n")
     
 def handle_destination_label (self):
    outFile = self.outFile
    extra_data = []
    # find next line
    i = self.i + 1
    next = self.linesd[i]
    while not next.isAssembler:
        i = i + 1
        next = self.linesd[i]
    outFile.write ("L" + next.address + ":\n")

 def determine_instruction_and_handle (self, ldata):
     """LineData : ldata"""
     if not ldata.isAssembler:
         outFile.write (ldata.full_text)
         #self.handle_default ()
     else:
         self.instr_to_func[ldata.instruction] ()

 def handle_add (self):
     self.outFile.write ("    %s += %s;\n" % \
                    (self.current.args[0], self.current.args[1]))

 def handle_and (self):
     self.outFile.write ("    %s = %s & %s;\n" % \
            (self.current.args[0], self.current.args[0], self.current.args[1]))

 def handle_cmp_test (self):
     outFile = self.outFile
     can_fill_in = TRUE
     arg0 = self.current.args[0]
     arg1 = self.current.args[1]
     i = self.i + 1
     while 1:
         if i >= len(self.linesd):
             can_fill_in = FALSE
             break
         n = self.linesd[i]
         if not n.isAssembler:
             i = i + 1
             continue
         elif n.instruction == "jmp":
             can_fill_in = FALSE
             break
         elif n.instruction[0] == "j":  # jge, jle, etc...
             can_fill_in = TRUE
             break
         elif n.instruction in ("push",):
             pass # ok
         elif n.instruction in ("mov", "lea"):
             # these are allowed instructions, now check if they are ok
             if n.args[0] == arg0  or  n.args[0] == arg1:
                 can_fill_in = FALSE
                 break
         else:  # don't know how to handle this instruction
             can_fill_in = FALSE
             break
         i = i + 1
     if not can_fill_in:
         self.handle_default ()
         return
     instr = n.instruction
     comparison = ""
     signType = ""  # "" , "(unsigned) ", "(signed) "
     if instr in ("ja", "jnbe"):
         comparison = ">"
         signType = "(unsigned) "
     elif instr in ("jg", "jnle"):
         comparison = ">"
         signType = "(signed) "

     elif instr in ("jae", "jnb", "jnc"):
         comparison = ">="
         signType = "(unsigned) "
     elif instr in ("jge", "jnl"):
         comparison = ">="
         signType = "(signed) "

     elif instr in ("jb", "jc", "jnae"):
         comparison = "<"
         signType = "(unsigned) "
     elif instr in ("jl", "jnge"):
         comparison = "<"
         signType = "(signed) "

     elif instr in ("jbe", "jna"):
         comparison = "<="
         signType = "(unsigned) "
     elif instr in ("jle", "jng"):
         comparison = "<="
         signType = "(signed) "

     elif instr in ("je", "jz"):
         comparison = "=="
         signType = ""
     elif instr in ("jne", "jnz"):
         comparison = "!="
         signType = ""
     else:
         raise "unknown comparison", instr

     c = self.current
     jmp_instr = instr

     if i - self.i > 1:
         #for j in range(self.i + 1, i):
         for j in range(1, i - self.i):
             self.i = self.i + 1
             if self.debug:
                 self.outFile.write (">>#>>" + self.linesd[self.i].full_text)
                 self.outFile.write ("\n")
             self.current = self.linesd[self.i]
             self.determine_instruction_and_handle (self.linesd[self.i])
     self.i = self.i + 1

     if c.instruction == "cmp":
         outFile.write ("    if (%s%s %s %s%s)  // %s %s,%s\n" % \
                        (signType, c.args[0], comparison, signType, c.args[1],
                         c.address, c.instruction, jmp_instr))
         outFile.write ("        goto L%s;\n" % n.args[0])
     elif c.instruction == "test":
         if c.args[0] == c.args[1]:
             outFile.write ("    if (%s%s %s %s0)  // %s %s,%s\n" % \
                            (signType, c.args[0], comparison, signType,
                             c.address, c.instruction, jmp_instr))
             outFile.write ("        goto L%s;\n" % n.args[0])
         else:
             outFile.write ("    if (%s%s & %s%s %s %s0)  // %s %s,%s\n" % \
                            (signType, c.args[0], signType, c.args[1],
                             comparison, signType, c.address, c.instruction,
                             jmp_instr))
             outFile.write ("        goto L%s;\n" % n.args[0])
     
 def handle_dec (self):
     self.outFile.write ("    %s--;\n" % self.current.args[0])

 def handle_DWORD (self):
     self.outFile.write ("; " + self.current.full_text)
     
 def handle_inc (self):
     self.outFile.write ("    %s++;\n" % self.current.args[0])

 def handle_jmp (self):
     if self.current.args[0][0] == "0":
         self.outFile.write ("    goto L%s;\n" % self.current.args[0][len("0x"):])
     else:
         self.outFile.write ("    goto %s;\n" % self.current.args[0])

 def handle_lea (self):
     c = self.current
     self.outFile.write ("    %s = %s;\n" % (c.args[0], c.args[1]))
     
 def handle_mov (self):
     self.outFile.write ("    %s = %s;\n" % \
                    (self.current.args[0], self.current.args[1]))
     
 def handle_or (self):
     if self.current.args[1] == "-1":
         self.outFile.write ("    %s = -1;\n" % self.current.args[0])
     else:
         self.outFile.write ("    %s = %s | %s;\n" % \
            (self.current.args[0], self.current.args[0], self.current.args[1]))

 def handle_ret (self):
     self.outFile.write ("    return eax;\n")

 def handle_sub (self):
     self.outFile.write ("    %s -= %s;\n" % \
                    (self.current.args[0], self.current.args[1]))

 def handle_xor (self):
     if self.current.args[0] == self.current.args[1]:
         self.outFile.write ("    %s = 0;\n" % self.current.args[0])
     else:
         #FIXME
         self.handle_default ()
         
 def run (self):
    inFile = self.inFile
    outFile = self.outFile
    
    lines = inFile.readlines ()
    self.linesd = []
    for line in lines:
        self.linesd.append (LineData (line))

    self.i = 0
    while self.i < len(self.linesd):
        self.current = self.linesd[self.i]
        instr = self.current.instruction

        if self.debug:
            self.outFile.write (">>" + self.current.full_text)
        if not self.current.isAssembler:
            if self.current.full_text[:len("---------")] == "---------":
                self.handle_destination_label ()
            else:
                outFile.write (self.current.full_text)
        elif instr == "add":
            self.handle_add ()
        elif instr == "and":
            self.handle_and ()
        elif instr == "cmp":
            self.handle_cmp_test ()
        elif instr == "dec":
            self.handle_dec ()
        elif instr == "DWORD":
            self.handle_DWORD ()
        elif instr == "inc":
            self.handle_inc ()
        elif instr == "jmp":
            self.handle_jmp ()
        elif instr == "lea":
            self.handle_lea ()
        elif instr == "mov":
            self.handle_mov ()
        elif instr == "or":
            self.handle_or ()
        elif instr == "ret":
            self.handle_ret ()
        elif instr == "sub":
            self.handle_sub ()
        elif instr == "test":
            self.handle_cmp_test ()
        elif instr == "xor":
            self.handle_xor ()
        else:
            self.handle_default ()

        self.i = self.i + 1
