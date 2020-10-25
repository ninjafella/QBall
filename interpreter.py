from tokens import token
import check
from copy import deepcopy
import lexer
import os

class dictionary(dict):
  def __init__(self):
    self = dict(self)
  
  def add(self, key, value):
    self[key] = value

  def remove(self, key):
    try:
      del self[key]
    except KeyError:
      pass

class object():
  def __init__(self, args: list, funcs: list):
    self.args = args
    self.funcs = funcs
    self.local = dictionary()
    self.global_ = dictionary()

global_vars = dictionary()
local_vars = dictionary()
function = dictionary()
arg = dictionary()
argvars = dictionary()
# All reserved keywords that use "end"
ends = ["for", "while", "if", "elif", "else"]

class interpreter:
  def __init__(self, toks, func=False):
    self.toks = iter(toks)
    self.func = func
    self.advance()

  def advance(self):
    try:
      self.tok = next(self.toks)
    except StopIteration:
      self.tok = None

  def arg(self):
    value = ""
    if self.tok.type in (token.TokenTypes.dquote, token.TokenTypes.squote):
      self.advance()
      value = self.tok.value
      self.advance()
      self.advance()
    elif self.tok.type in (token.TokenTypes.integer, token.TokenTypes.floating):
      value = self.tok.value
      self.advance()
    elif self.tok.value in global_vars:
      value = global_vars[self.tok.value]
      self.advance()
    elif self.tok.value in local_vars:
      value = local_vars[self.tok.value]
      self.advance()
    elif self.tok.type == token.TokenTypes.lbrack:
      self.advance()
      value = []
      while self.tok is not None and self.tok.type != token.TokenTypes.rbrack:
        a = self.arg()
        value.append(a)
        self.advance()
      self.advance()
    else:
      raise Exception("Illegal argument")
    return value

  # Since both functions and if/for/etc use end, this handles that
  def ends_in_func(self):
    toks = []
    while self.tok is not None and self.tok.value != "end":
      if self.tok.value in ends:
        toks.append(self.tok)
        self.advance()
        e = self.ends_in_func()
        for i in e:
          toks.append(i)
      toks.append(self.tok)
      self.advance()
    return toks

  def interpret(self):
    global arg
    while self.tok is not None:
      if self.tok.type == token.TokenTypes.builtin:
        if self.tok.value.lower() == "out":
          self.advance()
          to_print = []
          sep = " "
          while self.tok is not None and self.tok.type is not token.TokenTypes.semi:
            if self.tok.type in (token.TokenTypes.dquote, token.TokenTypes.squote):
              self.advance()
              to_print.append(self.tok.value)
              self.advance()
              self.advance()
            elif self.tok.value in global_vars:
              to_print.append(str(global_vars[self.tok.value]))
              self.advance()
            elif self.tok.value in local_vars:
              to_print.append(str(local_vars[self.tok.value]))
              self.advance()
            elif self.tok.value == "sep":
              self.advance()
              if self.tok.type == token.TokenTypes.equal:
                self.advance()
                if self.tok.value in global_vars:
                  sep = global_vars[self.tok.value]
                  self.advance()
                elif self.tok.type in (token.TokenTypes.squote,token.TokenTypes.dquote):
                  self.advance()
                  sep = self.tok.value
                  self.advance()
                  self.advance()
            elif self.tok.type in (token.TokenTypes.integer, token.TokenTypes.floating):
              to_print.append(str(self.tok.value))
              self.advance()
            else:
              raise Exception("Illegal arguement to out")
          print(sep.join(to_print))
          if self.tok is not None and self.tok.type == token.TokenTypes.semi:
            self.advance()
        elif self.tok.value.lower() == "global":
          self.advance()
          name = self.tok.value
          self.advance()
          if self.tok is None or self.tok.type == token.TokenTypes.semi:
            value = ""
          elif self.tok.type == token.TokenTypes.equal:
            self.advance()
            value = self.arg()
            self.advance() if self.tok is not None and self.tok.type in (token.TokenTypes.dquote, token.TokenTypes.squote) else print(end="")
          if self.tok is not None and self.tok.type != token.TokenTypes.semi:
            raise Exception("Must have ; or EOF after variable decleration")
          if self.tok is not None and self.tok.type == token.TokenTypes.semi:
            self.advance()
          global_vars.add(name, value)
        elif self.tok.value.lower() == "local" and self.func is True:
          self.advance()
          name = self.tok.value
          self.advance()
          if self.tok is None or self.tok.type == token.TokenTypes.semi:
            value = ""
          elif self.tok.type == token.TokenTypes.equal:
            self.advance()
            value = self.arg()
            self.advance() if self.tok.type in (token.TokenTypes.dquote, token.TokenTypes.squote) else print(end="")
          if self.tok is not None and self.tok.type != token.TokenTypes.semi:
            raise Exception("Must have ; or EOF after variable decleration")
          if self.tok is not None and self.tok.type == token.TokenTypes.semi:
            self.advance()
          local_vars.add(name, value)
        elif self.tok.value.lower() == "local":
          raise Exception("Local outside of function")
        elif self.tok.value in function:
          funcname = self.tok.value
          self.advance()
          for i in arg[funcname]:
            value = ""
            if self.tok.value in local_vars:
              value = local_vars[self.tok.value]
              argvars.add(i, ["local", self.tok.value])
              self.advance()
            elif self.tok.value in global_vars:
              value = global_vars[self.tok.value]
              argvars.add(i, ["global", self.tok.value])
              self.advance()
            else:
              value = self.arg()
            local_vars.add(i, value)
          interpreter(function[funcname], True).interpret()
          for i in arg[funcname]:
            local_vars.remove(i)
          if self.tok is not None and self.tok.type != token.TokenTypes.semi:
            raise Exception("Expected ; or EOL")
          if self.tok is not None and self.tok.type == token.TokenTypes.semi:
            self.advance()
        elif self.tok.value == "free":
          self.advance()
          if self.tok.value in global_vars:
            global_vars.remove(self.tok.value)
          elif self.tok.value in local_vars:
              local_vars.remove(self.tok.value)
              self.advance()
          else:
            raise Exception("Expected var arguement")
          self.advance()
          if self.tok is not None and self.tok.type != token.TokenTypes.semi:
            raise Exception("free takes one arguement only")
          if self.tok is not None and self.tok.type == token.TokenTypes.semi:
            self.advance()
        elif self.tok.value == "memcop":
          self.advance()
          var1 = self.tok.value
          self.advance()
          var2 = self.tok.value
          self.advance()
          if var2 in global_vars:
            if var1 in global_vars:
              global_vars[var2] = deepcopy(global_vars[var1])
            elif var1 in local_vars:
              global_vars[var2] = deepcopy(local_vars[var1])
            else:
              raise Exception("Cannot have var1 as a value, must be variable")
          elif var2 in local_vars:
            if var1 in global_vars:
              local_vars[var2] = deepcopy(global_vars[var1])
            elif var1 in local_vars:
              local_vars[var2] = deepcopy(local_vars[var1])
            else:
              raise Exception("Cannot have var1 as a value, must be variable")
          else:
            raise Exception("var2 must be a variable, not a value")
        elif self.tok.value == "str":
          self.advance()
          if self.tok.value in global_vars:
            global_vars[self.tok.value] = str(global_vars[self.tok.value])
            self.advance()
          elif self.tok.value in local_vars:
              local_vars[self.tok.value] = str(global_vars[self.tok.value])
              self.advance()
          if self.tok is not None and self.tok.type != token.TokenTypes.semi:
            raise Exception("No EOL")
          if self.tok is not None and self.tok.type == token.TokenTypes.semi:
            self.advance()
        elif self.tok.value == "int":
          self.advance()
          if self.tok.value in global_vars:
            global_vars[self.tok.value] = int(global_vars[self.tok.value])
            self.advance()
          elif self.tok.value in local_vars:
              local_vars[self.tok.value] = int(global_vars[self.tok.value])
              self.advance()
          if self.tok is not None and self.tok.type != token.TokenTypes.semi:
            raise Exception("No EOL")
          if self.tok is not None and self.tok.type == token.TokenTypes.semi:
            self.advance()
        elif self.tok.value == "type":
          # Do this tomorrow
          pass
        elif self.tok.value == "sys":
          self.advance()
          a = self.arg()
          os.system(a)
          if self.tok.type in (token.TokenTypes.squote, token.TokenTypes.dquote):
            self.advance()
          if self.tok is not None and self.tok.type != token.TokenTypes.semi:
            raise Exception("No ; or EOL")
          if self.tok is not None and self.tok.type == token.TokenTypes.semi:
            self.advance()
        elif self.tok.value == "id":
          # This is the equivelent of "out &var"
          self.advance()
          if self.tok.value in global_vars:
            print(str(hex(id(global_vars[self.tok.value])))[1:])
          elif self.tok.value in local_vars:
              print(str(hex(id(local_vars[self.tok.value])))[1:])
          self.advance()
          if self.tok is not None and self.tok.type != token.TokenTypes.semi:
            raise Exception("No EOL")
          if self.tok is not None and self.tok.type == token.TokenTypes.semi:
            self.advance()
        elif self.tok.value.lower() == "for":
          self.advance()
          name = self.tok.value
          self.advance()
          if self.tok.value != "in":
            raise Exception("for loop with no in")
          self.advance()
          iterobj = self.arg()
          self.advance() if self.tok.type in (token.TokenTypes.dquote, token.TokenTypes.squote) else print(end="")
          if self.tok.type != token.TokenTypes.semi:
            raise Exception("No ; in for loop")
          self.advance()
          toks = []
          while self.tok is not None and self.tok.value != "end":
            if self.tok.value in ends:
              e = self.ends_in_func()
              for i in e:
                toks.append(i)
            else:
              toks.append(self.tok)
              self.advance()
          self.advance()
          for i in iterobj:
            global_vars.add(name, i)
            if self.func:
              interpreter(toks, True).interpret()
            else:
              interpreter(toks).interpret()
          global_vars.remove(name)
        elif self.tok.value == "pass":
          self.advance()
          if self.tok is not None and self.tok.type != self.tok.type != token.TokenTypes.semi:
            raise Exception("Expected ; or EOL")
          if self.tok is not None:
            self.advance()
          continue
        elif self.tok.value == "return" and self.func:
          self.advance()
          name = self.tok.value
          globalv = True if argvars[name][0] == "global" else False
          self.advance()
          val = self.arg()
          if globalv:
            global_vars[name] = val
          else:
            local_vars[name] = val
          self.advance()
          if self.tok is not None and self.tok.type != self.tok.type != token.TokenTypes.semi:
            raise Exception("Expected ; or EOL")
          if self.tok is not None:
            self.advance()
        elif self.tok.value == "return":
          raise Exception("return outside of function")
        elif self.tok.value == "import":
          self.advance()
          name = f"../stdlib/{self.tok.value}"
          raw_name = self.tok.value
          self.advance()
          try:
            if not os.path.exists(name) and raw_name not in os.listdir("../stdlib") and raw_name not in os.listdir(os.getcwd()) and f"{raw_name}.qball" not in os.listdir(os.getcwd()):
              raise Exception("Unrecognized file")
            elif os.path.exists(name):
              importopen = open(name).read()
              tokens = lexer(importopen)
              interpreter(tokens).interpret()
            elif raw_name in os.listdir("../stdlib"):
              importopen = open(f"../stdlib/{raw_name}/main.qball").read()
              tokens = lexer(importopen)
              interpreter(tokens).interpret()
            elif raw_name in os.listdir():
              importopen = open(f"{raw_name}/main.qball").read()
              tokens = lexer(importopen)
              interpreter(tokens).interpret()
            else:
              importopen = open(f"{raw_name}.qball").read()
              tokens = lexer(importopen)
              interpreter(tokens).interpret()
          except FileNotFoundError:
            if f"{raw_name}.qball" not in os.listdir(os.getcwd()) and raw_name not in os.listdir():
              raise Exception("Unrecognized file")
            elif f"{raw_name}.qball" in os.listdir(f"{raw_name}.qball"):
              importopen = open(name).read()
              tokens = lexer(importopen)
              interpreter(tokens).interpret()
            elif raw_name in os.listdir(os.getcwd()):
              importopen = open(f"{raw_name}/main.qball").read()
              tokens = lexer(importopen)
              interpreter(tokens).interpret()
          if self.tok is not None and self.tok.type != self.tok.type != token.TokenTypes.semi:
            raise Exception("Expected ; or EOL")
          if self.tok is not None:
            self.advance()
        elif self.tok.value == "py":
          self.advance()
          arg = self.arg()
          x = compile(arg, "python", "exec")
          exec(x)
          self.advance()
          if self.tok is not None and self.tok.type != self.tok.type != token.TokenTypes.semi:
            raise Exception("Expected ; or EOL")
          if self.tok is not None:
            self.advance()
        elif self.tok.value == "qstr":
          self.advance()
          arg = self.arg()
          self.advance()
          tokens = lexer.lexer(arg).generate_tokens()
          interpreter(tokens).interpret()
          if self.tok is not None and self.tok.type != self.tok.type != token.TokenTypes.semi:
            raise Exception("Expected ; or EOL")
          if self.tok is not None:
            self.advance()
        else:
          raise Exception(f"Illegal function {self.tok.value}")
      elif self.tok.type == token.TokenTypes.underscore:
        self.advance()
        func_name = self.tok.value
        self.advance()
        args = []
        toks = []
        while self.tok.type != token.TokenTypes.semi:
          args.append(self.tok.value)
          self.advance()
        arg.add(func_name, args)
        self.advance()
        while self.tok is not None and self.tok.value != "end":
          if self.tok.value in ends:
            e = self.ends_in_func()
            for i in e:
              toks.append(i)
          else:
            toks.append(self.tok)
            self.advance()
        self.advance()
        function.add(func_name, toks)
      elif self.tok.type in (token.TokenTypes.squote, token.TokenTypes.dquote):
        self.advance()
        self.advance()
        self.advance()
      else:
        raise Exception("Illegal token")
