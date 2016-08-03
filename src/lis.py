#! /usr/bin/env python3
# -*- coding: utf-8 -*-

'A lisp(Scheme subset) interpreter in Python'

import math
import operator as op

# A Scheme Symbol is implemented as a Python str
Symbol = str
# A Scheme List is implemented as a Python list
List = list
# A Scheme Number is implemented as a Python int or float
Number = (int, float)
# An environment is a mapping of {variable: value}

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


class Env(dict):
    """
    An environment: a dict of {'var': val} pairs, with an outer Env.
    """
    def __init__(self, parms=(), args=(), outer=None):
        self.update(zip(parms, args))
        self.outer = outer

    def find(self, var):
        """
        Find the innermost Env where var appears.
        """
        return self if (var in self) else self.outer.find(var)  # There is a potential bug


class Procedure():
    """
    A user-defined Scheme procedure
    """
    def __init__(self, parms, body, env):
        self.parms, self.body, self.env = parms, body, env

    def __call__(self, *args):
        return eval(self.body, Env(self.parms, args, self.env))


global_env = standard_env()


def tokenize(chars):
    """
    Convert a string of characters into a list tokens.
    """
    return chars.replace('(', ' ( ').replace(')', ' ) ').split()


def atom(token):
    """
    Numbers become numbers; every other token is a symbeol.
    """
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return Symbol(token)


def read_from_tokens(tokens):
    """
    Read an expression from a sequence of tokens
    """
    if len(tokens) == 0:
        raise SyntaxError('unexpected EOF while reading')
    token = tokens.pop(0)
    if token == '(':
        L = []
        while tokens[0] != ')':
            L.append(read_from_tokens(tokens))
        tokens.pop(0) # pop off ')'
        return L
    elif token == ')':
        raise SyntaxError('unexpected )')
    else:
        return atom(token)


def parse(program):
    """
    Read a Scheme expression for a string.
    """
    return read_from_tokens(tokenize(program))


def eval(x, env=global_env):
    """
    Evaluate an expression in environment
    """
    if isinstance(x, Symbol):  # variable reference
        return env.find(x)[x]
    elif not isinstance(x, List):  # constant literal
        return x
    elif x[0] == 'quote':  # quotation
        (_, exp) = x
        return exp
    elif x[0] == 'if':  # conditional
        (_, test, conseq, alt) = x
        exp = (conseq if eval(test, env) else alt)
        return eval(exp, env)
    elif x[0] == 'define':  # definition
        (_, var, exp) = x
        env[var] = eval(exp, env)
    elif x[0] == 'set!':  # assignment
        (_, var, exp) = x
        env.find(var)[var] = eval(exp, env)
    elif x[0] == 'lambda':  # procedure
        (_, parms, body) = x
        return Procedure(parms, body, env)
    else:  # procedure call
        proc = eval(x[0], env)
        args = [eval(arg, env) for arg in x[1:]]
        return proc(*args)

def repl(prompt='lis.py> '):
    """
    A prompt-read-eval-print loop.
    """
    while True:
        code = input(prompt)
        if code == 'exit()':
            return
        val = eval(parse(code))
        if val is not None:
            print(schemestr(val))


def schemestr(exp):
    """
    Convert a Python object back into as Scheme-readable string.
    """
    if isinstance(exp, list):
        return '(' + ''.join(map(schemestr, exp)) + ')'
    else:
        return str(exp)


def main():
    "Only for test"
    program = "(define r 10)"
    ans = eval(parse(program))
    ans = eval(parse("(* pi (* r r))"))
    print(ans)

if __name__ == '__main__':
    main()
