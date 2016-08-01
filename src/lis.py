#! /usr/bin/env python3
# -*- coding: utf-8 -*-

'A lisp interpreter in Python'

import math
import operator as op

# A Scheme Symbol is implemented as a Python str
Symbol = str
# A Scheme List is implemented as a Python list
List = list
# A Scheme Number is implemented as a Python int or float
Number = (int, float)
# An environment is a mapping of {variable: value}
Env = dict

def standard_env():
    """
    An environment with some Scheme standard procedures.
    """
    env = Env()
    env.update(vars(math))
    env.update({
        '+':op.add, '-':op.sub, '*',op.mul, '/',op.div,
        '>':op.gt, '<':op.lt, '>=':op.ge, '<=': op.le, '=':op.eq,
        'abs': abs,
        'append': op.add,
        'apply': apply,
        'begin': lambda *x: x[-1],
        'car': lambda x: x[0],
        'cdr': lambda x: x[1:],
        'cons': lambda x,y: [x] + y,
        'eq?': op.is_,
        'equal?': op.eq,
        'length': len,
        'list': lambda *x: list[x]
        'list?' lambda x: isinstance(x, list)

    })

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


def main():
    "Only for test"
    program = "(begin (define r 10) (* pi (* r r)))"
    print(parse(program))

if __name__ == '__main__':
    main()