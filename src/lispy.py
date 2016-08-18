#! /usr/bin/env python3
# -*- coding: utf-8 -*-

'A lisp(Scheme subset) interpreter in Python'

import operator as op
import re
import sys
import math
# Symbol, Procedure, classes

class Symbol(str):
    pass


def Sym(s, symbol_table={}):
    """
    Find or create unique Symbol entry for str s in symbol table.
    """
    if s not in symbol_table:
        symbol_table[s] = Symbol(s)
    return symbol_table[s]


_quote, _if, _set, _define, _lambda, _begin, _definemacro = map(Sym,
                                                                 "quote if set! define lambda begin define-macro".split())

_quasiquote, _unquote, _unquotesplicing = map(Sym,
                                              "quasiquote unquote unquote-splicing".split())


# parse, read and user interaction

def tokenize(chars):
    """
    Convert a string of characters into a list tokens.
    """
    return chars.replace('(', ' ( ').replace(')', ' ) ').split()

def parse(inport):
    """
    Read a Scheme expression for a string.
    """
    return read(inport)


eof_object = Symbol('#<eof-object>')

class InPort():
    """
    An input port. Retains a line of chars.
    """
    tokenizer = r'''\s*(,@|[('`,)]|"(?:[\\].|[^\\"])*"|;.*|[^\s('"`,;)]*)(.*)'''
    def __init__(self, file):
        self.file = file
        self.line = ''

    def next_token(self):
        """
        Return the next token, reading new text into line buffer if needed.
        """
        while True:
            if self.line == '':
                self.line = self.file.readline()
            if self.line == '':
                return eof_object
            token, self.line = re.match(InPort.tokenizer, self.line).groups()
            if token != '' and not token.startswith(';'):
                return token

def readchar(inport):
    """
    Read the next character from an input port.
    """
    if inport.line != '':
        ch, inport.line = inport.line[0], inport.line[1]
        return ch
    else:
        return inport.file.read(1) or eof_object

def read(inport):
    """
    Read a Scheme expression from an input port.
    """
    def read_ahead(token):
        if token == '(':
            L = []
            while True:
                token = inport.next_token()
                if token == ')':
                    return L
                else:
                    L.append(read_ahead(token))
        elif token == ')':
            raise SyntaxError('unexpected )')
        elif token in quotes:
            return [quotes[token], read(inport)]
        elif token in eof_object:
            raise SyntaxError('unexpected EOF in list')
        else:
            return atom(token)
    # body of read:
    token1 = inport.next_token()
    return eof_object if token1 is eof_object else read_ahead(token1)


quotes = {"'":_quote, "`":_quasiquote, ",":_unquote, ",@":_unquotesplicing}

def atom(token):
    """
    Numbers become numbers: #t and #f are booleans; "..." string; otherwise Symbol.
    """
    if token == '#t':
        return True
    elif token == '#f':
        return False
    elif token[0] == '"':
        return token[1:-1].decode('unicode_escape')
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            try:
                return complex(token.replace('i', 'j', 1))
            except ValueError:
                return Sym(token)

def to_string(x):
    """
    Convert a python object back into a Lisp-readable string.
    """
    if x is True:
        return '#t'
    elif x is False:
        return '#f'
    elif isinstance(x, Symbol):
        return x
    elif isinstance(x, str):
        return "%s" % x.encode('unicode_escape').replace('"', r'\"')
    elif isinstance(x, list):
        return '(' + ''.join(map(to_string, x)) + ')'
    elif isinstance(x, complex):
        return str(x).replace('j', 'i')
    else:
        return str(x)

def load(filename):
    """
    Eval every expression from a file
    """
    sys.stderr.write("Lispy version 2.0\n")
    repl(None, InPort(filename), None)

def repl(prompt='lispy> ', inport=InPort(sys.stdin), out=sys.stdout):
    """
    A prompt-read-eval-print loop
    """
    print("Lispy version 2.0")
    while True:
        try:
            if prompt:
                print(prompt, end='', flush=True)
            x = parse(inport)
            if x is eof_object:
                return
            val = eval(x)
            if val is not None and out:
                print(out, to_string(val))
        except Exception as e:
            print("%s %s" % (type(e).__name__, e))


# Environment class

class Env(dict):
    """
    An environment: a dict of {'var': val} pairs, with an outer Env.
    """
    def __init__(self, parms=(), args=(), outer=None):
        # Bind parm list to corresponding args, or single parm to list of args
        self.outer = outer
        if isinstance(parms, Symbol):
            self.update({parms:list(args)})
        else:
            if len(args) != len(parms):
                raise TypeError('expected %s, given %s, ' % (to_string(parms), to_string(args)))
        self.update(zip(parms, args))

    def find(self, var):
        """
        Find the innermost Env where var appears.
        """
        if var in self:
            return self
        elif self.outer is None:
            raise LookupError(var)
        else:
            return self.outer.find(var)

def cons(x, y):
    return [x] + y

def standard_env():
    """
    An environment with some Scheme standard procedures.
    """
    env = Env()
    env.update(vars(math))
    env.update({
        '+':op.add, '-':op.sub, '*':op.mul, '/':op.truediv,
        '>':op.gt, '<':op.lt, '>=':op.ge, '<=': op.le, '=':op.eq,
        'abs': abs,
        'append': op.add,
        'begin': lambda *x: x[-1],
        'car': lambda x: x[0],
        'cdr': lambda x: x[1:],
        'cons': lambda x, y: [x] + y,
        'eq?': op.is_,
        'equal?': op.eq,
        'length': len,
        'list': lambda *x: list(x),
        'list?': lambda x: isinstance(x, list),
        'map': map,
        'max': max,
        'min': min,
        'not': op.not_,
        'null?': lambda x: x == [],
        'number?': lambda x: isinstance(x, Number),
        'procedure?': callable,
        'round': round,
        'symbol?': lambda x: isinstance(x, Symbol),
    })
    return env

global_env = standard_env()


# eval (tail recursive)

# A Scheme List is implemented as a Python list
List = list
# A Scheme Number is implemented as a Python int or float
Number = (int, float)

def eval(x, env=global_env):
    """
    Evaluate an expression in environment
    """
    while True:
        if isinstance(x, Symbol):  # variable reference
            return env.find(x)[x]
        elif not isinstance(x, List):  # constant literal
            return x
        elif x[0] is _quote:  # quotation
            (_, exp) = x
            return exp
        elif x[0] is _if:  # conditional
            (_, test, conseq, alt) = x
            x = (conseq if eval(test, env) else alt)
        elif x[0] is _set:  # assignment
            (_, var, exp) = x
            env.find(var)[var] = eval(exp, env)
            return None
        elif x[0] is _define:  # definition
            (_, var, exp) = x
            env[var] = eval(exp, env)
            return None
        elif x[0] is _lambda:  # (lambda (var*) exp)
            (_, parms, exp) = x
            return Procedure(parms, exp, env)
        elif x[0] is _begin:  # (begin exp+)
            for exp in x[1:-1]:
                eval(exp, env)
            x = x[-1]
        else:  # (proc exp*)
            exps = [eval(exp, env) for exp in x]
            proc = exps.pop(0)
            if isinstance(proc, Procedure):
                x = proc.exp
                env = Env(proc.parms, exps, proc.env)
            else:
                return proc(*exps)


class Procedure():
    """
    A user-defined Scheme procedure.
    """
    def __init__(self, parms, exp, env):
        self.parms, self.exp, self.env = parms, exp, env

    def __call__(self, *args):
        return eval(self.exp, Env(self.parms, args, self.env))


# expand

def expand(x, toplevel=False):
    """
    Walk tree of x, making optimization/fixes, and signaling Syntax Error.
    """
    pass

def require(x, predicate, msg="wrong length"):
    """
    Signal a syntax error if predicate is false.
    """
    if not predicate:
        raise SyntaxError(to_string(x) + ": " + msg)



def let(*args):
    args = list(args)
    x = cons(_let, args)
    require(x, len(args) > 1)
    bindings, body = args[0], args[1:]
    require(x, all(isinstance(b, list) and len(b) == 2 and isinstance(b[0], Symbol) for b in bindings), "illegal binding list")
    vars, vals = zip(*bindings)
    return [[_lambda, list(vars)] + map(expand, body)] + map(expand, vals)

_append, _cons, _let = map(Sym, "append cons let".split())

macro_table = {_let: let}  # More macros can go here

eval(parse("""(begin

(define-macro and (lambda args
   (if (null? args) #t
       (if (= (length args) 1) (car args)
           `(if ,(car args) (and ,@(cdr args)) #f)))))

;; More macros can go here

)"""))


def callcc(proc):
    """
    Call proc with current continuation; escape only
    """
    ball = RuntimeWarning("Sorry, can't continue this continuation any longer.")
    def throw(retval):
        ball.retval = retval;
        raise ball
    try:
        return proc(throw)
    except RuntimeWarning as w:
        if w is ball:
            return ball.retval
        else:
            raise w


if __name__ == '__main__':
    repl()
