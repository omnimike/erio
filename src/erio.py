#!/usr/bin/env python3
import string
import io
import sys
import operator
from collections import namedtuple

class ErioError(Exception): pass
class ErioSyntaxError(ErioError): pass
class ErioLexerError(ErioError): pass
class ErioInvalidTokenError(ErioLexerError): pass
class ErioRuntimeError(ErioError): pass

Token = namedtuple('Token', ('type', 'value'))

keywords = {'if', 'then', 'else', 'end-if', 'while', 'do', 'end-while',
            'def', 'end-def', 'return', 'or', 'and', 'not'}
symbols = {'(':     'open-paren',
           ')':     'close-paren',
           ',':     'comma',
           '=':     'assignment',
           '[':     'open-bracket',
           ']':     'close-bracket',
           '>':     'gt',
           '<':     'lt',
           '>=':    'gteq',
           '<=':    'lteq',
           '==':    'eq',
           '!=':    'noteq',
           '+':     'add',
           '-':     'sub',
           '*':     'mul',
           '/':     'div',
           '%':     'mod'}
tests = {
    'boolean':      lambda s: s in ('true','false'),
    'identifier':   lambda s: s.isidentifier(),
    'integer':      lambda s: s.isdigit(),
    'string':       lambda s: s.startswith('"')
                          and s.endswith('"')
                          and s.isprintable()}
quote = '"'

def make_token(value):
    if value in keywords:
        return Token(value, value)
    elif value in symbols:
        return Token(symbols[value], value)
    else:
        for name, test in tests.items():
            if test(value):
                return Token(name, value)
    raise ErioInvalidTokenError(value)

def tokenize(stream):
    '''Creates a generator which returns the tokens from the stream'''

    buffer = ''
    instring = False
    for c in stream:
        if instring and c != quote:
           buffer += c
           continue
        if c == quote:
            if instring:
                instring = False
                buffer += c
                yield make_token(buffer)
                buffer = ''
                continue
            else:
                instring = True
        #Make sure to check for multi-char symbols
        if buffer in symbols and buffer + c not in symbols:
            yield make_token(buffer)
            buffer = c.strip()
            continue
        #We have found the end of a token if we have hit whitespace or the
        #beginning of a symbol. We check to make sure we are not currently
        #reading in a multi-char symbol before we split.
        #We test for 'end' so that the '-' symbol doesn't split 'end-x'
        #keywords.
        if len(buffer) > 0 and (c.isspace() or \
                (c in [s[0] for s in symbols] \
                 and buffer + c not in symbols \
                 and buffer != 'end')):
            yield make_token(buffer)
            buffer = ''
        buffer += c.strip()
    if len(buffer) > 0:
        yield make_token(buffer)
        buffer = ''

IfStmnt = namedtuple('IfStmnt', ('cond', 'then', 'els'))
WhileStmnt = namedtuple('WhileStmnt', ('cond', 'do'))
AssignmentStmnt = namedtuple('AssignmentStmnt', ('id', 'expr'))
ConstantExpr = namedtuple('ConstantExpr', ('value'))
VariableExpr = namedtuple('VariableExpr', ('id'))
SequenceExpr = namedtuple('SequenceExpr', ('value'))
FunctionCall = namedtuple('FunctionCall', ('id', 'args'))
FunctionDef = namedtuple('FunctionDef', ('id', 'args', 'body'))
ReturnStmnt = namedtuple('ReturnStmnt', ('value'))
AddExpr = namedtuple('AddExpr', ('op', 'lhs', 'rhs'))
MulExpr = namedtuple('MulExpr', ('op', 'lhs', 'rhs'))
OrExpr = namedtuple('OrExpr', ('op', 'lhs', 'rhs'))
AndExpr = namedtuple('AndExpr', ('op', 'lhs', 'rhs'))
NotExpr = namedtuple('NotExpr', ('op', 'rhs'))
CompExpr = namedtuple('CompExpr', ('op', 'lhs', 'rhs'))
SignExpr = namedtuple('SignExpr', ('op', 'rhs'))

def parse(stream):
    token = next(stream)
    lookahead = next(stream)
    def next_token():
        nonlocal token, lookahead
        token = lookahead
        lookahead = next(stream, Token('eof', None))

    def top_level_statement():
        if token.type == 'return':
            raise ErioSyntaxError('Return statement outside of function body')
        else:
            return statement()

    def statement():
        if token.type == 'if':
            return if_stmnt()
        elif token.type == 'while':
            return while_stmnt()
        elif token.type == 'def':
            return function_def()
        elif token.type == 'return':
            return return_stmnt()
        elif token.type == 'identifier':
            if lookahead.type == 'assignment':
                return assignment_stmnt()
            elif lookahead.type == 'open-paren':
                return function_call()
        raise ErioSyntaxError(token)

    def function_call():
        name = token
        next_token() #identifier
        next_token() #open-paren
        args = []
        while token.type != 'close-paren':
            args.append(expr())
            if token.type == 'comma':
                next_token() #comma
        next_token() #close-paren
        return FunctionCall(name, args)

    def function_def():
        next_token() #def
        name = token
        next_token() #identifier
        next_token() #open-paren
        args = []
        while token.type != 'close-paren':
            args.append(token)
            next_token() #identifier
            if token.type == 'comma':
                next_token() #comma
        next_token() #close-paren
        body = []
        while token.type != 'end-def':
            body.append(statement())
        next_token() #end-def
        return FunctionDef(name, args, body)

    def return_stmnt():
        next_token() #return
        return ReturnStmnt(expr())

    def if_stmnt():
        next_token() #if
        cond = expr()
        next_token() #then
        then = []
        while token.type not in ('else', 'end-if'):
            then.append(statement())
        els = []
        if token.type == 'else':
            next_token() #else
            while token.type != 'end-if':
                els.append(statement())
        next_token() #end-if
        return IfStmnt(cond, then, els)

    def while_stmnt():
        next_token() #while
        cond = expr()
        next_token() #do
        do = []
        while token.type != 'end-while':
            do.append(statement())
        next_token() #end-while
        return WhileStmnt(cond, do)

    def assignment_stmnt():
        var = token
        next_token() #identifier
        next_token() #assignment operator
        value = expr()
        return AssignmentStmnt(var, value)

    def expr():
        def make_left_assoc_binary_op(expr_type, next_expr, token_types):
            def binary_op():
                def build_tree(lhs):
                    if token.type not in token_types:
                        return lhs
                    op = token
                    next_token() #op keyword
                    exp = expr_type(op, lhs, next_expr())
                    return build_tree(exp)
                return build_tree(next_expr())
            return binary_op

        def make_prefix_unary_op(expr_type, next_expr, token_types):
            def unary_op():
                op_token_list = []
                while token.type in token_types:
                    op = token
                    next_token() #op keyword
                    op_token_list.append(op)
                exp = next_expr()
                for op in reversed(op_token_list):
                    exp = expr_type(op, exp)
                return exp
            return unary_op

        sign_expr = make_prefix_unary_op(
            SignExpr, atom, ('add', 'sub'))
        mul_expr = make_left_assoc_binary_op(
            MulExpr, sign_expr, ('mul', 'div', 'mod'))
        add_expr = make_left_assoc_binary_op(
            AddExpr, mul_expr, ('add', 'sub'))
        comp_expr = make_left_assoc_binary_op(
            CompExpr, add_expr, ('eq', 'gt', 'lt', 'gteq', 'lteq', 'noteq'))
        not_expr = make_prefix_unary_op(
            NotExpr, comp_expr, ('not'))
        and_expr = make_left_assoc_binary_op(
            AndExpr, not_expr, ('and'))
        or_expr = make_left_assoc_binary_op(
            OrExpr, and_expr, ('or'))
        return or_expr()

    def atom():
        if token.type in ('string', 'integer', 'boolean'):
            return constant_expr()
        elif token.type == 'identifier':
            if lookahead.type == 'open-paren':
                return function_call()
            else:
                return variable_expr()
        elif token.type == 'open-bracket':
            return sequence_expr()
        elif token.type == 'open-paren':
            return enclosure_expr()
        raise ErioSyntaxError(token)

    def constant_expr():
        val = token
        next_token() #constant
        return ConstantExpr(val)

    def variable_expr():
        val = token
        next_token() #identifier
        return VariableExpr(val)

    def sequence_expr():
        next_token() #open-bracket
        elements = []
        while token.type != 'close-bracket':
            elements.append(expr())
            if token.type == 'comma':
                next_token() #comma
        next_token() #close-bracket
        return SequenceExpr(elements)

    def enclosure_expr():
        next_token() #open-paren
        exp = expr()
        next_token() #close-paren
        return exp

    while token.type != 'eof':
        yield top_level_statement()

Integer = namedtuple('Integer', 'val')
String = namedtuple('String', 'val')
Boolean = namedtuple('Boolean', 'val')
Sequence = namedtuple('Sequence', 'val')
Function = namedtuple('Function', ('env', 'args', 'body'))

class Namespace(dict):
    def __init__(self, *args, parent=None):
        super().__init__(*args)
        self.parent = parent

    def __getitem__(self, key):
        if not super().__contains__(key) \
                and self.parent != None and key in self.parent:
            return self.parent[key]
        return super().__getitem__(key)

    def __contains__(self, key):
        found_here = super().__contains__(key)
        if not found_here \
                and self.parent != None and key in self.parent:
            return True
        return found_here

def build_global_environment(out):
    env = Namespace()
    env['.out'] = out

    def primitive_function(name, argnames):
        def decor(original_func):
            env[name] = Function(env, argnames, original_func)
            return original_func
        return decor

    @primitive_function('print', ['s'])
    def _print(runenv):
        s = ''
        if isinstance(runenv['s'], Boolean):
            s = 'true' if runenv['s'].val else 'false'
        else:
            s = str(runenv['s'].val)
        runenv['.out'].write(s)

    @primitive_function('add', ['lhs', 'rhs'])
    def _add(runenv):
        return Integer(runenv['lhs'].val + runenv['rhs'].val)

    @primitive_function('sub', ['lhs', 'rhs'])
    def _sub(runenv):
        return Integer(runenv['lhs'].val - runenv['rhs'].val)

    @primitive_function('lt', ['lhs', 'rhs'])
    def _lt(runenv):
        return Boolean(runenv['lhs'].val < runenv['rhs'].val)

    @primitive_function('eq', ['lhs', 'rhs'])
    def _eq(runenv):
        return Boolean(runenv['lhs'].val == runenv['rhs'].val)

    @primitive_function('geti', ['seq', 'i'])
    def _geti(runenv):
        return runenv['seq'].val[runenv['i'].val]

    @primitive_function('seti', ['seq', 'i', 'value'])
    def _seti(runenv):
        runenv['seq'].val[runenv['i'].val] = runenv['value']

    @primitive_function('len', ['seq'])
    def _len(runenv):
        return Integer(len(runenv['seq'].val))

    @primitive_function('insert', ['seq', 'i', 'value'])
    def _insert(runenv):
        runenv['seq'].val.insert(runenv['i'].val, runenv['value'])

    return env

def execute(env, block):
    def true(obj):
        return obj.val == True

    def exec_block(block):
        #ret might hold the return value for a function. We jump out of the
        #block if that happens.
        for s in block:
            ret = exec_statement(s)
            if ret: return ret

    def exec_statement(statement):
        #if and while can cause functions to return if they contain 'return's
        #themselves. Other statements (besides return itself) cannot do this.
        ret = None
        if isinstance(statement, IfStmnt):
            ret = exec_if(statement)
        elif isinstance(statement, WhileStmnt):
            ret = exec_while(statement)
        elif isinstance(statement, ReturnStmnt):
            ret = exec_return(statement)
        elif isinstance(statement, AssignmentStmnt):
            exec_assign(statement)
        elif isinstance(statement, FunctionCall):
            eval_func_call(statement)
        elif isinstance(statement, FunctionDef):
            exec_func_def(statement)
        return ret

    def exec_if(statement):
        if true(eval_expr(statement.cond)):
            ret = exec_block(statement.then)
            if ret: return ret
        else:
            ret = exec_block(statement.els)
            if ret: return ret

    def exec_while(statement):
        while true(eval_expr(statement.cond)):
            ret = exec_block(statement.do)
            if ret: return ret

    def exec_assign(statement):
        env[statement.id.value] = eval_expr(statement.expr)

    def exec_func_def(func_def):
        name = func_def.id.value
        args = [token.value for token in func_def.args]
        def func(runenv):
            return execute(runenv, func_def.body)
        env[name] = Function(env, args, func)

    def exec_return(statement):
        return eval_expr(statement.value)

    def eval_expr(expr):
        if isinstance(expr, ConstantExpr):
            return eval_const(expr.value)
        elif isinstance(expr, VariableExpr):
            return eval_var(expr.id)
        elif isinstance(expr, SequenceExpr):
            return eval_seq(expr.value)
        elif isinstance(expr, OrExpr):
            return eval_or(expr)
        elif isinstance(expr, AndExpr):
            return eval_and(expr)
        elif isinstance(expr, NotExpr):
            return eval_not(expr)
        elif isinstance(expr, CompExpr):
            return eval_comp(expr)
        elif isinstance(expr, (MulExpr, AddExpr)):
            return eval_arith(expr)
        elif isinstance(expr, SignExpr):
            return eval_sign(expr)
        elif isinstance(expr, FunctionCall):
            return eval_func_call(expr)
        else:
            raise ErioRuntimeError('Invalid expression: {}'.format(expr))

    def eval_or(expr):
        lhs = eval_expr(expr.lhs)
        if true(lhs):
            return lhs
        rhs = eval_expr(expr.rhs)
        if true(rhs):
            return rhs
        return Boolean(False)

    def eval_and(expr):
        lhs = eval_expr(expr.lhs)
        if not true(lhs):
            return Boolean(False)
        rhs = eval_expr(expr.rhs)
        if not true(rhs):
            return Boolean(False)
        return rhs

    def eval_not(expr):
        return Boolean(not true(eval_expr(expr.rhs)))

    def eval_comp(expr):
        ops = {
            'eq':       operator.eq,
            'lt':       operator.lt,
            'gt':       operator.gt,
            'lteq':     operator.le,
            'gteq':     operator.ge,
            'noteq':    operator.ne}
        lhs = eval_expr(expr.lhs).val
        rhs = eval_expr(expr.rhs).val
        return Boolean(ops[expr.op.type](lhs, rhs))

    def eval_arith(expr):
        ops = {
            'add':  operator.add,
            'sub':  operator.sub,
            'mul':  operator.mul,
            'div':  operator.floordiv,
            'mod':  operator.mod}
        lhs = eval_expr(expr.lhs).val
        rhs = eval_expr(expr.rhs).val
        return Integer(ops[expr.op.type](lhs, rhs))

    def eval_sign(expr):
        ops = {
            'add':  operator.pos,
            'sub':  operator.neg}
        rhs = eval_expr(expr.rhs).val
        return Integer(ops[expr.op.type](rhs))

    def eval_func_call(func_call):
        func = env[func_call.id.value]
        evald_args = [eval_expr(a) for a in func_call.args]
        runenv = Namespace(parent=func.env)
        runenv.update(zip(func.args, evald_args))
        return func.body(runenv)

    def eval_const(token):
        if token.type == 'string':
            #Strip the quotes off the string before returning it
            return String(token.value[1:-1])
        elif token.type == 'integer':
            return Integer(int(token.value))
        elif token.type == 'boolean':
            return Boolean(token.value == 'true')
        else:
            raise ErioRuntimeError('Invalid constant token: {}'.format(token))

    def eval_var(token):
        return env[token.value]

    def eval_seq(elems):
        return Sequence([eval_expr(e) for e in elems])

    return exec_block(block)

def exec_to_string(block):
    out = io.StringIO()
    env = build_global_environment(out)
    execute(env, block)
    result = out.getvalue()
    out.close()
    return result

def exec_to_stdout(block):
    out = sys.stdout
    env = build_global_environment(out)
    execute(env, block)

def interpreter(instream, outstream):
    def by_char(stream):
        for line in stream:
            for char in line:
                yield char
    env = build_global_environment(outstream)
    execute(env, parse(tokenize(by_char(instream))))

def erio(text):
    exec_to_stdout(parse(tokenize(text)))

if __name__ == '__main__':
    interpreter(sys.stdin, sys.stdout)
    pass


