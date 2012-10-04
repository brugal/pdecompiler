#!/usr/bin/env python
import string

TRUE = 1
FALSE = 0

def check_hex (text):
    if len(text) == 0:
        return text
    if text[0] in ("-", "+"):
        sign_mark = text[0]
        text = text[1:]
    else:
        sign_mark = ""

    # if text.orig in ("+", "-")
    if len(text) == 0:
        return sign_mark
    # check if it's in hex form
    if text[:2] == "0x"  or  text[:2] == "0X":
        text = text[2:]
    # strip leading zeroes
    for i in range(len(text)):
        if text[i] != "0":
            break
    text = text[i:]

    if text[0] not in string.hexdigits:
        return sign_mark + text
    try:
        num = string.atol (text, 16)
        if num > 9:
            return sign_mark + "0x" + text
        else:
            return sign_mark + text
    except ValueError, message:
        return sign_mark + text
    
def parse_mem_ref (text):
    """takes something of the form dword[ebp + eax * 4 + 10005666] and
    returns ["dword", "+", "eax", "*", "4", "0x10005666"]
    """
    tokens = ("[", "+", "-", "*", "]")
    breaks = []
    for i in range(len(text)):
        if text[i] in tokens:
            breaks.append (i)
    words = []
    words.append (text[:breaks[0]])
    i = 0
    while i < len(breaks) - 1:
        words.append (text[breaks[i]])
        words.append (text[breaks[i] + 1 : breaks[i + 1]])
        i = i + 1
    words.append (text[breaks[i]])
    for i in range(len(words)):
        words[i] = check_hex (words[i])
    return words

def strip_comas (word):
    if word[0] == ",":
        word = word[1:]
    if word[-1] == ",":
        word = word[:-1]
    return word

class LineData:
    """parses lines of the form:
       :10004C1C 89442418                mov dword[esp+18], eax ; stack + 0,
       sldkfj
    """
    def __init__ (self, line):
        self.full_text = None
        self.isAssembler = FALSE
        self.address = None
        self.opcode = None
        self.instruction = None
        self.args = []
        self.comments = None
        
        if line[0] != ":":
            self.isAssembler = FALSE
            self.full_text = line
            return
        else:
            self.isAssembler = TRUE
            line = line[1:]  # strip leading ":"
            self.full_text = line
            
        # find comments
        for i in range(len(line)):
            if line[i] == ";":
                self.comments = string.strip (line[i + 1:])
                line = line[:i]
                break
                
        words = string.split (line)
        self.address = words[0]
        self.opcode = words[1]
        self.instruction = words[2]
        
        # get self.args[]
        if len(words) > 3:
            self.args = string.split (string.join(words[3:],""), ",")
            for i in range(len(self.args)):
                self.args[i] = strip_comas (self.args[i])
                
        # check if comments override args
        args_override = []
        for i in range(len(self.args)):
            args_override.append (None)
        if self.comments:
            x = string.split (self.comments, ",")
            for i in range(len(x)):
                x[i] = string.strip (x[i])
                if x[i] != "":
                    args_override[i] = x[i]
        
        if self.instruction in ("cmp", "test", "add", "sub", "mov", "and", 
                                "or", "sar", "shr", "shl", "jmp"):
            for i in range(len(self.args)):
                if self.args[i] == None:
                    continue
                # ex: mov eax, dword[10003000]
                if "[" in self.args[i]:  # need to check for hex conversions
                    arg_tokens = parse_mem_ref (self.args[i])
                    if arg_tokens[0] in ("dword", "byte", "word"):
                        # ex: mov dword[0x1001002], eax
                        if len(arg_tokens) == 4:  # 'dword', '[', '0x111', ']'
                            if arg_tokens[0] == "dword":
                                typecast = ""
                            elif arg_tokens[0] == "byte":
                                typecast = "*(byte *)"
                            elif arg_tokens[0] == "word":
                                typecast = "*(word *)"
                            else:
                                raise Exception, "invalid mem size"
                            if typecast == "":
                                if args_override[i] != None:
                                    self.args[i] = args_override[i]
                                elif arg_tokens[2][:2] == "0x":
                                    self.args[i] = "*V" + \
                                                   arg_tokens[2][len("0x"):]
                                else:
                                    self.args[i] = "*" + arg_tokens[2]
                            else:
                                if args_override[i] != None:
                                    self.args[i] = typecast + " %s" % \
                                                   args_override[i]
                                elif arg_tokens[2][:2] == "0x":
                                    self.args[i] = typecast + " V" + \
                                                   arg_tokens[2][len("0x"):]
                                else:
                                    #self.args[i] = typecast + " %s" % \
                                    #               arg_tokens[2][len("0x"):]
                                    self.args[i] = typecast + " %s" % \
                                                   arg_tokens[2]
                        # ex: mov eax, dword[esp + 0xc] ; , arg1
                        elif     args_override[i] != None  and  \
                                 args_override[i][:len("stack")] != "stack":
                            if arg_tokens[0] == "dword":
                                typecast = ""
                            elif arg_tokens[0] == "byte":
                                typecast = "*(byte *)"
                            elif arg_tokens[0] == "word":
                                typecast = "*(word *)"

                            if typecast == "":
                                self.args[i] = args_override[i]
                            else:
                                self.args[i] = typecast + args_override[i]
                        else:
                            if arg_tokens[0] == "dword":
                                #typecast =  "*(dword *)"
                                typecast = "*"
                            elif arg_tokens[0] == "word":
                                typecast = "*(word *)"
                            elif arg_tokens[0] == "byte":
                                typecast = "*(byte *)"
                            else:
                                raise Exception, "what the fuck"
                            # ex: mov ebx, dword[esp + 0x1c] ; , stack + 0xc
                            if args_override[i] != None:
                                self.args[i] = typecast + "(%s)" % \
                                               args_override[i]
                            else:
                                self.args[i] = typecast + "(%s)" % \
                                             string.join(arg_tokens[2:-1], " ")
                    else:
                        self.args[i] = string.join (arg_tokens)
                else:
                    self.args[i] = check_hex (self.args[i])
        if self.instruction == "lea":  # lea eax, dword[ebx+ecx*4+100]
            if args_override[1] != None:
                self.args[1] = args_override[1]
            else:
                # [ 'dword', '[', etc.., ']' ]  becomes:  [ etc... ]
                tokens = parse_mem_ref(self.args[1])[2:-1]
                new_arg = []
                for t in tokens:
                    new_arg.append (check_hex(t))
                self.args[1] = string.join (new_arg, " ")
                
    def printx (self):
        print "(A) %s (O) %s (C) %s (a0) %s (a1) %s (a2) %s (comm) %s" % \
              (self.address, self.opcode, self.instruction, self.args[0],
               self.args[1], self.args[2], self.comments)

