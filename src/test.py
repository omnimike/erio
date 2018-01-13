import unittest
from erio import *

class TokenizerTests(unittest.TestCase):
    '''Test cases for the erio tokenizer'''

    def test_tokenizer(self):
        '''Tests the tokenizer with valid arguments'''
        test_string = '''
            if then else end-if while do end-while = 100 some_string
            ("a string") [false, true ] def return end-def or and not
            > < >= <= == != + - * / %'''
        expected_results = [
            ('if',              'if'),
            ('then',            'then'),
            ('else',            'else'),
            ('end-if',          'end-if'),
            ('while',           'while'),
            ('do',              'do'),
            ('end-while',       'end-while'),
            ('assignment',      '='),
            ('integer',         '100'),
            ('identifier',      'some_string'),
            ('open-paren',      '('),
            ('string',          '"a string"'),
            ('close-paren',     ')'),
            ('open-bracket',    '['),
            ('boolean',         'false'),
            ('comma',           ','),
            ('boolean',         'true'),
            ('close-bracket',   ']'),
            ('def',             'def'),
            ('return',          'return'),
            ('end-def',         'end-def'),
            ('or',              'or'),
            ('and',             'and'),
            ('not',             'not'),
            ('gt',              '>'),
            ('lt',              '<'),
            ('gteq',            '>='),
            ('lteq',            '<='),
            ('eq',              '=='),
            ('noteq',           '!='),
            ('add',             '+'),
            ('sub',             '-'),
            ('mul',             '*'),
            ('div',             '/'),
            ('mod',             '%')]
        it = tokenize(test_string)
        for t, v in expected_results:
            token = next(it)
            self.assertEqual(token.type, t)
            self.assertEqual(token.value, v)

        self.assertRaises(StopIteration, next, it)

class ParserTests(unittest.TestCase):
    '''Test for the erio parser'''

    def test_parser(self):
        '''Tests the parser with a syntactically correct program'''
        program = parse(tokenize(r'''
                test = true
                if test then
                    total = 1
                else
                    total = 2
                end-if
                count = 0
                while lt(count, total) do
                    print("hello", "world!")
                    count = add(count, 1)
                end-while
                array = [1, 2]'''))
        expected_results = [
            AssignmentStmnt(Token('identifier', 'test'),
                                ConstantExpr(Token('boolean', 'true'))),
            IfStmnt(VariableExpr(Token('identifier', 'test')),
                        [AssignmentStmnt(Token('identifier', 'total'),
                                            ConstantExpr(Token('integer', '1')))],
                        [AssignmentStmnt(Token('identifier', 'total'),
                                            ConstantExpr(Token('integer', '2')))]),
            AssignmentStmnt(Token('identifier', 'count'),
                            ConstantExpr(Token('integer', '0'))),
            WhileStmnt(FunctionCall(Token('identifier', 'lt'),
                                        [VariableExpr(Token('identifier', 'count')),
                                         VariableExpr(Token('identifier', 'total'))]),
                           [FunctionCall(Token('identifier', 'print'),
                                        [ConstantExpr(Token('string', '"hello"')),
                                         ConstantExpr(Token('string', '"world!"'))]),
                            AssignmentStmnt(Token('identifier', 'count'),
                                                FunctionCall(Token('identifier', 'add'),
                                                             [VariableExpr(Token('identifier', 'count')),
                                                              ConstantExpr(Token('integer', '1'))]))]),
            AssignmentStmnt(Token('identifier', 'array'),
                                SequenceExpr([
                                    ConstantExpr(Token('integer', '1')),
                                    ConstantExpr(Token('integer', '2'))]))]
        results = list(program)
        self.assertListEqual(results, expected_results)
        self.assertRaises(StopIteration, next, program)

    def test_parse_function_def(self):
        '''Tests the parser to see if it can handle function declarations'''
        program = parse(tokenize(r'''
                def useradd(x, y)
                    return add(x, y)
                end-def'''))
        expected_results = [
            FunctionDef(Token('identifier', 'useradd'),
                                [Token('identifier', 'x'),
                                 Token('identifier', 'y')],
                                [ReturnStmnt(FunctionCall(
                                    Token('identifier', 'add'),
                                    [VariableExpr(Token('identifier', 'x')),
                                     VariableExpr(Token('identifier', 'y'))]))])]
        results = list(program)
        self.assertListEqual(results, expected_results)
        self.assertRaises(StopIteration, next, program)

    def test_numeric_operators(self):
        ''' Tests the parsing of infix numeric operators'''
        program = parse(tokenize(r'''
                x = 1 + 1
                x = 1- 1
                x = 1 *1
                x = 1/1
                x=1%1'''))
        expected_results = [
            AssignmentStmnt(Token('identifier', 'x'),
                            AddExpr(Token('add', '+'),
                                    ConstantExpr(Token('integer', '1')),
                                    ConstantExpr(Token('integer', '1')))),
            AssignmentStmnt(Token('identifier', 'x'),
                            AddExpr(Token('sub', '-'),
                                    ConstantExpr(Token('integer', '1')),
                                    ConstantExpr(Token('integer', '1')))),
            AssignmentStmnt(Token('identifier', 'x'),
                            MulExpr(Token('mul', '*'),
                                    ConstantExpr(Token('integer', '1')),
                                    ConstantExpr(Token('integer', '1')))),
            AssignmentStmnt(Token('identifier', 'x'),
                            MulExpr(Token('div', '/'),
                                    ConstantExpr(Token('integer', '1')),
                                    ConstantExpr(Token('integer', '1')))),
            AssignmentStmnt(Token('identifier', 'x'),
                            MulExpr(Token('mod', '%'),
                                    ConstantExpr(Token('integer', '1')),
                                    ConstantExpr(Token('integer', '1'))))]
        results = list(program)
        self.assertListEqual(results, expected_results)
        self.assertRaises(StopIteration, next, program)

    def test_comparison_operators(self):
        ''' Tests the parsing of infix comparison operators'''
        program = parse(tokenize(r'''
                x = 1 == 1
                x = 1> 1
                x =1 <1
                x=  1>=1
                x = 1  <=  1
                x=1!=1'''))
        expected_results = [
            AssignmentStmnt(Token('identifier', 'x'),
                            CompExpr(Token('eq', '=='),
                                     ConstantExpr(Token('integer', '1')),
                                     ConstantExpr(Token('integer', '1')))),
            AssignmentStmnt(Token('identifier', 'x'),
                            CompExpr(Token('gt', '>'),
                                     ConstantExpr(Token('integer', '1')),
                                     ConstantExpr(Token('integer', '1')))),
            AssignmentStmnt(Token('identifier', 'x'),
                            CompExpr(Token('lt', '<'),
                                     ConstantExpr(Token('integer', '1')),
                                     ConstantExpr(Token('integer', '1')))),
            AssignmentStmnt(Token('identifier', 'x'),
                            CompExpr(Token('gteq', '>='),
                                     ConstantExpr(Token('integer', '1')),
                                     ConstantExpr(Token('integer', '1')))),
            AssignmentStmnt(Token('identifier', 'x'),
                            CompExpr(Token('lteq', '<='),
                                     ConstantExpr(Token('integer', '1')),
                                     ConstantExpr(Token('integer', '1')))),
            AssignmentStmnt(Token('identifier', 'x'),
                            CompExpr(Token('noteq', '!='),
                                     ConstantExpr(Token('integer', '1')),
                                     ConstantExpr(Token('integer', '1'))))]
        results = list(program)
        self.assertListEqual(results, expected_results)
        self.assertRaises(StopIteration, next, program)

    def test_logic_operators(self):
        ''' Tests the parsing of infix logic operators'''
        program = parse(tokenize(r'''
                x = true and false
                x = true or false
                x = not false'''))
        expected_results = [
            AssignmentStmnt(Token('identifier', 'x'),
                            AddExpr(Token('and', 'and'),
                                    ConstantExpr(Token('boolean', 'true')),
                                    ConstantExpr(Token('boolean', 'false')))),
            AssignmentStmnt(Token('identifier', 'x'),
                            OrExpr(Token('or', 'or'),
                                    ConstantExpr(Token('boolean', 'true')),
                                    ConstantExpr(Token('boolean', 'false')))),
            AssignmentStmnt(Token('identifier', 'x'),
                            NotExpr(Token('not', 'not'),
                                    ConstantExpr(Token('boolean', 'false'))))]
        results = list(program)
        self.assertListEqual(results, expected_results)
        self.assertRaises(StopIteration, next, program)

    def test_order_of_operations(self):
        '''Tests operator precedence for logic, comparison and arithmetic operators'''
        program = parse(tokenize(r'''
                test = x == 1 and y * 2 - 4 < 3 or not 5 != z % 6'''))
        expected_results = [
            AssignmentStmnt(Token('identifier', 'test'),
                            OrExpr(Token('or', 'or'),
                                    AndExpr(Token('and', 'and'),
                                            CompExpr(Token('eq', '=='),
                                                    VariableExpr(Token('identifier', 'x')),
                                                    ConstantExpr(Token('integer', '1'))),
                                            CompExpr(Token('lt', '<'),
                                                     AddExpr(Token('sub', '-'),
                                                             MulExpr(Token('mul', '*'),
                                                                     VariableExpr(Token('identifier', 'y')),
                                                                     ConstantExpr(Token('integer', '2'))),
                                                             ConstantExpr(Token('integer', '4'))),
                                                     ConstantExpr(Token('integer', '3')))),
                                   NotExpr(Token('not', 'not'),
                                           CompExpr(Token('noteq', '!='),
                                                    ConstantExpr(Token('integer', '5')),
                                                    MulExpr(Token('mod', '%'),
                                                            VariableExpr(Token('identifier', 'z')),
                                                            ConstantExpr(Token('integer', '6')))))))]

        results = list(program)
        self.assertListEqual(results, expected_results)
        self.assertRaises(StopIteration, next, program)

    def test_negative_integers(self):
        '''Tests the parsing of negative integers'''
        program = parse(tokenize(r'''
                x = -55
                y = 55 + - x'''))
        expected_results = [
            AssignmentStmnt(Token('identifier', 'x'),
                            SignExpr(Token('sub', '-'),
                                     ConstantExpr(Token('integer', '55')))),
            AssignmentStmnt(Token('identifier', 'y'),
                            AddExpr(Token('add', '+'),
                                    ConstantExpr(Token('integer', '55')),
                                    SignExpr(Token('sub', '-'),
                                             VariableExpr(Token('identifier', 'x')))))]
        results = list(program)
        self.assertListEqual(results, expected_results)
        self.assertRaises(StopIteration, next, program)

    def test_enclosure(self):
        '''Tests the parsing of expressions grouped by parenthesis'''
        program = parse(tokenize(r'''
                x = (1 + 2) * 3'''))
        expected_results = [
            AssignmentStmnt(Token('identifier', 'x'),
                            MulExpr(Token('mul', '*'),
                                    AddExpr(Token('add', '+'),
                                            ConstantExpr(Token('integer', '1')),
                                            ConstantExpr(Token('integer', '2'))),
                                    ConstantExpr(Token('integer', '3'))))]
        results = list(program)
        self.assertListEqual(results, expected_results)
        self.assertRaises(StopIteration, next, program)

class EvaluatorTests(unittest.TestCase):
    '''Tests for the erio evaluator'''

    def test_hello_world(self):
        '''Tests the execution of a single function call'''
        program = 'print("hello world")'
        expected_result = 'hello world'
        result = exec_to_string(parse(tokenize(program)))
        self.assertEqual(result, expected_result)

    def test_simple_program(self):
        '''Tests a simple program'''
        program = r'''
                test = true
                if test then
                    total = add(4, 3)
                else
                    total = 3
                end-if
                count = 0
                a = ["this", "was", "a"]
                insert(a, len(a), "triumph")
                print(geti(a, 3))
                while lt(count, total) do
                    print("!")
                    count = add(count, 1)
                end-while'''
        expected_result = 'triumph!!!!!!!'
        result = exec_to_string(parse(tokenize(program)))
        self.assertEqual(result, expected_result)

    def test_function_def(self):
        '''Tests the declaration and execution of a function'''
        program = r'''
                def mul(x, y)
                    c = 0
                    a = 0
                    while lt(c, y) do
                        a = add(a, x)
                        c = add(c, 1)
                    end-while
                    return a
                end-def
                print(mul(6, 7))'''
        expected_result = '42'
        result = exec_to_string(parse(tokenize(program)))
        self.assertEqual(result, expected_result)

    def test_order_of_operations(self):
        '''Test that operators are applied in the right order'''
        program = r'''
                x = 7==1 and 10/5 <= 11 or 8*2-4 > -15 or not 5 != 9 % 6
                print(x)'''
        expected_result = 'true'
        result = exec_to_string(parse(tokenize(program)))
        self.assertEqual(result, expected_result)

    def test_enclosure(self):
        '''Test expressions grouped by parenthesis'''
        program = r'''
                print((1 + 2) * 3)'''
        expected_result = '9'
        result = exec_to_string(parse(tokenize(program)))
        self.assertEqual(result, expected_result)

if __name__ == '__main__':
    unittest.main(exit=False)
