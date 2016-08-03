#! /usr/bin/env python3
# -*- coding: utf-8 -*-

'A lisp(Scheme subset) interpreter in Python'

# 数据的内部表示，数据的操作，读写语法
"""
ports: Ouput ports用Python file objects表示， input ports用一个类InputPort包装一个file object和记录已读取文本的最近一行。这很方便，因为Scheme的input ports需要读入表达式和原生字符和我们的Tokennizer作用于一整行，不是单独的字符。

'exp: (quote exp)
`exp
,exp: insert the value of exp
@exp: 
"""

import re
import sys

class Symbol(str):
    pass


def Sym(s, symbol_table={}):
    """
    Find or create unique Symbol entry for str s in symbol table.
    """
    if s not in symbol_table:
        symbol_table[s] = Symbol(s)
    return symbol_table[s]


_quote, _if, _set, _define, _lambda, _begin, _definemacro = map(Sym, "quote if set! define lambda begin define-macro".split())

_quasiquote, _unquote, _unquotesplicing = map(Sym, "quote if set! define lambda begin define-macro".split())


eof_object = Symbol('#<eof-object>')

class InPort():
    """
    An input port. Retains a line of chars.
    """
    tokenizer = r'''
    \s*(,@ | [('`,)] | "(?:[\\]. | [^\\"])*" | ;.* | [^\s('"`,;)]*)(.*)
    '''
    # ,@   ' ` ,        "(
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
            if token != '' and not token.startwith(';'):
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
    Convert a python object back into a Liso-readable string.
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

def repl(prompt='listy> ', inport=InPort(sys.stdin), out=sys.stdout):
    """
    A prompt-read-eval-print loop
    """
    sys.stderr.write("Lispy version 2.0\n")
    while True:
        try:
            if prompt:
                sys.stderr.write(prompt)
                x = parse(inport)
            if x is eof_object:
                return
            val = eval(x)
            if val is not None and out:
                print(out, to_string(val))
        except Exception as e:
            print("%s %s" % (type(e).__name__, e))


if __name__ == '__main__':
    repl()
