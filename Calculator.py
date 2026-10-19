import math
import os
import sys


# =====================================================================
# 1. TOKEN VE LEXER (DÜZELTİLMİŞ KELİME AYRIŞTIRICI İLE)
# =====================================================================

class Token:
    def __init__(self, type, value=None, line=1, col=1):
        self.type = type
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"{self.type}:{self.value} (Line:{self.line}, Col:{self.col})"


class Lexer:
    DIGIT = ".0123456789"
    SINGLE_OPERATORS = "+-*/^=><!"
    LPARAN = "("
    RPARAN = ")"
    LBRACE = "{"
    RBRACE = "}"
    LBRACKET = "["
    RBRACKET = "]"
    COMMA = ","

    def __init__(self, text):
        self.text = text
        self.pos = -1
        self.start = 0
        self.line = 1
        self.col = 0
        self.current_token = None

    def nextpos(self):
        self.pos += 1
        if self.pos < len(self.text):
            if self.text[self.pos] == '\n':
                self.line += 1
                self.col = 0
            else:
                self.col += 1
            return self.pos
        return None

    def getchar(self):
        if 0 <= self.pos < len(self.text):
            return self.text[self.pos]
        return ""

    def peekchar(self):
        if self.pos + 1 < len(self.text):
            return self.text[self.pos + 1]
        return ""

    def token_gen(self, tok_type, tok_start, tok_width):
        tok_col = max(1, self.col - tok_width + 1)
        if tok_start == -1:
            self.current_token = Token(tok_type, "\0", self.line, self.col)
        else:
            val = self.text[tok_start:tok_start + tok_width]
            self.current_token = Token(tok_type, val, self.line, tok_col)
        return self.current_token

    def get_digitseq(self):
        if self.nextpos() is not None:
            if self.getchar().isdigit():
                while self.nextpos() is not None:
                    if self.getchar().isdigit():
                        continue
                    else:
                        break
                return True
        return False

    def fractionalconstant(self):
        optionel = self.get_digitseq()
        self.pos -= 1
        if self.nextpos() is not None:
            if self.getchar() != ".":
                self.pos -= 1
                return False
            if not optionel:
                temp = self.get_digitseq()
                self.pos -= 1
                return temp
            self.get_digitseq()
            self.pos -= 1
            return True
        else:
            self.pos -= 1
            return False

    def exponentpart(self):
        if self.nextpos() is not None:
            if self.getchar().upper() != "E":
                return False
            self.pos += 1
            if self.nextpos() is not None:
                if self.getchar() not in "+-":
                    self.pos -= 1
                else:
                    self.pos += 1
        return self.get_digitseq()

    def floatingliteral(self):
        if self.fractionalconstant():
            self.exponentpart()
            return True
        elif self.get_digitseq():
            self.pos -= 1
            return self.exponentpart()
        return False

    def get_token(self):
        while self.nextpos() is not None:
            char = self.getchar()

            if char == '\0' or ord(char) == 0:
                continue

            # Yorum Satırları (#)
            if char == '#':
                while self.nextpos() is not None:
                    if self.getchar() == '\n':
                        break
                continue

            # Metin / String Tanımı ("...")
            if char == '"':
                self.start = self.pos + 1
                start_col = self.col
                str_val = ""
                while self.nextpos() is not None:
                    c = self.getchar()
                    if c == '"':
                        break
                    str_val += c
                token = Token("String", str_val, self.line, start_col)
                self.current_token = token
                return token

            # Değişken ve Anahtar Kelimeler (and, or, not, break, continue)
            if char.isalpha() or char == '_':
                self.start = self.pos
                start_col = self.col
                while self.nextpos() is not None:
                    c = self.getchar()
                    if not (c.isalnum() or c == '_'):
                        break
                width = self.pos - self.start
                val = self.text[self.start:self.start + width]
                token = Token("IDENTIFIER", val, self.line, start_col)
                self.current_token = token
                self.pos -= 1
                return token

            # Sayılar
            if char in self.DIGIT:
                self.start = self.pos
                start_col = self.col
                self.pos -= 1
                tok_type = "Float" if self.floatingliteral() else "INT"
                width = self.pos - self.start
                token = Token(tok_type, self.text[self.start:self.start + width], self.line, start_col)
                self.current_token = token
                self.pos -= 1
                return token

            if char in self.LPARAN:
                return self.token_gen("LPARAN", self.pos, 1)

            if char in self.RPARAN:
                return self.token_gen("RPARAN", self.pos, 1)

            if char in self.LBRACE:
                return self.token_gen("LBRACE", self.pos, 1)

            if char in self.RBRACE:
                return self.token_gen("RBRACE", self.pos, 1)

            if char == self.LBRACKET:
                return self.token_gen("LBRACKET", self.pos, 1)

            if char == self.RBRACKET:
                return self.token_gen("RBRACKET", self.pos, 1)

            if char == self.COMMA:
                return self.token_gen("COMMA", self.pos, 1)

            # Çift karakterli operatörler (==, !=, >=, <=)
            if char in "!=><":
                next_c = self.peekchar()
                if next_c == "=":
                    self.start = self.pos
                    start_col = self.col
                    self.nextpos()
                    token = Token("Operator", self.text[self.start:self.start + 2], self.line, start_col)
                    self.current_token = token
                    return token
                elif char in "><":
                    return self.token_gen("Operator", self.pos, 1)

            if char in self.SINGLE_OPERATORS:
                return self.token_gen("Operator", self.pos, 1)

            if char.isspace():
                self.start = self.pos
                start_col = self.col
                while self.nextpos() is not None:
                    if not self.getchar().isspace():
                        break
                width = self.pos - self.start
                token = Token("Boşluk", self.text[self.start:self.start + width], self.line, start_col)
                self.current_token = token
                self.pos -= 1
                return token

            continue

        return Token("EOF", "\0", self.line, self.col)


# =====================================================================
# 2. AST DÜĞÜMLERİ VE KONTROL İSTİSNALARI
# =====================================================================

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class BreakException(Exception):
    pass

class ContinueException(Exception):
    pass


class ASTNode:
    pass

class NumNode(ASTNode):
    def __init__(self, value):
        self.value = float(value)

class StringNode(ASTNode):
    def __init__(self, value):
        self.value = str(value)

class VarNode(ASTNode):
    def __init__(self, name):
        self.name = name

class ListNode(ASTNode):
    def __init__(self, elements):
        self.elements = elements

class IndexAccessNode(ASTNode):
    def __init__(self, target, index_expr):
        self.target = target
        self.index_expr = index_expr

class IndexAssignNode(ASTNode):
    def __init__(self, target, index_expr, expr):
        self.target = target
        self.index_expr = index_expr
        self.expr = expr

class UnaryOpNode(ASTNode):
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

class BinOpNode(ASTNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class AssignNode(ASTNode):
    def __init__(self, var_name, expr):
        self.var_name = var_name
        self.expr = expr

class FunctionCallNode(ASTNode):
    def __init__(self, func_name, args=None):
        self.func_name = func_name
        self.args = args if args is not None else []

class FunctionDefNode(ASTNode):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class ReturnNode(ASTNode):
    def __init__(self, expr):
        self.expr = expr

class BreakNode(ASTNode):
    pass

class ContinueNode(ASTNode):
    pass

class BlockNode(ASTNode):
    def __init__(self, statements):
        self.statements = statements

class IfNode(ASTNode):
    def __init__(self, condition, then_branch, else_branch=None):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

class WhileNode(ASTNode):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


# =====================================================================
# 3. AST PARSER
# =====================================================================

class Parser:
    BUILTIN_FUNCTIONS = {"sin", "cos", "tan", "sqrt", "abs", "log", "print", "input", "len", "push", "pop"}

    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = None
        self.advance()

    def advance(self):
        while True:
            self.current_token = self.lexer.get_token()
            if self.current_token.type != "Boşluk":
                break

    def error(self, msg="Sözdizimi Hatası"):
        line = self.current_token.line
        col = self.current_token.col
        val = self.current_token.value
        raise SyntaxError(f"[Satır {line}, Sütun {col}] {msg} (Hatalı ifade: '{val}')")

    def parse(self):
        statements = []
        while self.current_token.type != "EOF":
            stmt = self.statement()
            if stmt is not None:
                statements.append(stmt)

        if not statements:
            return None

        return BlockNode(statements) if len(statements) > 1 else statements[0]

    def statement(self):
        if self.current_token.type == "IDENTIFIER":
            val = self.current_token.value
            if val == "def":
                return self.function_def()
            elif val == "return":
                return self.return_statement()
            elif val == "break":
                self.advance()
                return BreakNode()
            elif val == "continue":
                self.advance()
                return ContinueNode()
            elif val == "if":
                return self.if_statement()
            elif val == "while":
                return self.while_statement()

        if self.current_token.type == "LBRACE":
            return self.block()

        return self.assignment()

    def function_def(self):
        self.advance()

        if self.current_token.type != "IDENTIFIER":
            self.error("Fonksiyon ismi bekleniyor")
        func_name = self.current_token.value
        self.advance()

        if self.current_token.type != "LPARAN":
            self.error("Fonksiyon isminden sonra '(' bekleniyor")
        self.advance()

        params = []
        if self.current_token.type == "IDENTIFIER":
            params.append(self.current_token.value)
            self.advance()
            while self.current_token.type == "COMMA":
                self.advance()
                if self.current_token.type != "IDENTIFIER":
                    self.error("Virgülden sonra parametre ismi bekleniyor")
                params.append(self.current_token.value)
                self.advance()

        if self.current_token.type != "RPARAN":
            self.error("Parametre listesinden sonra ')' bekleniyor")
        self.advance()

        body = self.statement()
        return FunctionDefNode(func_name, params, body)

    def return_statement(self):
        self.advance()
        expr = self.expr()
        return ReturnNode(expr)

    def while_statement(self):
        self.advance()
        if self.current_token.type != "LPARAN":
            self.error("'while' sonrasında '(' bekleniyor")
        self.advance()

        condition = self.expr()

        if self.current_token.type != "RPARAN":
            self.error("Koşul sonrasında ')' bekleniyor")
        self.advance()

        body = self.statement()
        return WhileNode(condition, body)

    def if_statement(self):
        self.advance()
        if self.current_token.type != "LPARAN":
            self.error("'if' sonrasında '(' bekleniyor")
        self.advance()

        condition = self.expr()

        if self.current_token.type != "RPARAN":
            self.error("Koşul sonrasında ')' bekleniyor")
        self.advance()

        then_branch = self.statement()
        else_branch = None

        if self.current_token.type == "IDENTIFIER" and self.current_token.value == "else":
            self.advance()
            else_branch = self.statement()

        return IfNode(condition, then_branch, else_branch)

    def block(self):
        self.advance()
        statements = []

        while self.current_token.type not in ("RBRACE", "EOF"):
            stmt = self.statement()
            if stmt:
                statements.append(stmt)

        if self.current_token.type != "RBRACE":
            self.error("Blok sonunda '}' bekleniyor")
        self.advance()

        return BlockNode(statements)

    def assignment(self):
        expr_node = self.expr()

        if isinstance(expr_node, VarNode) and self.current_token.type == "Operator" and self.current_token.value == "=":
            self.advance()
            val_node = self.expr()
            return AssignNode(expr_node.name, val_node)

        if isinstance(expr_node, IndexAccessNode) and self.current_token.type == "Operator" and self.current_token.value == "=":
            self.advance()
            val_node = self.expr()
            return IndexAssignNode(expr_node.target, expr_node.index_expr, val_node)

        return expr_node

    def expr(self):
        return self.logical_or()

    def logical_or(self):
        node = self.logical_and()
        while self.current_token.type == "IDENTIFIER" and self.current_token.value == "or":
            op = self.current_token.value
            self.advance()
            node = BinOpNode(node, op, self.logical_and())
        return node

    def logical_and(self):
        node = self.equality()
        while self.current_token.type == "IDENTIFIER" and self.current_token.value == "and":
            op = self.current_token.value
            self.advance()
            node = BinOpNode(node, op, self.equality())
        return node

    def equality(self):
        node = self.comparison()
        while self.current_token.type == "Operator" and self.current_token.value in ("==", "!="):
            op = self.current_token.value
            self.advance()
            node = BinOpNode(node, op, self.comparison())
        return node

    def comparison(self):
        node = self.term()
        while self.current_token.type == "Operator" and self.current_token.value in (">", "<", ">=", "<="):
            op = self.current_token.value
            self.advance()
            node = BinOpNode(node, op, self.term())
        return node

    def term(self):
        node = self.factor()
        while self.current_token.type == "Operator" and self.current_token.value in ("+", "-"):
            op = self.current_token.value
            self.advance()
            node = BinOpNode(node, op, self.factor())
        return node

    def factor(self):
        node = self.power()
        while self.current_token.type == "Operator" and self.current_token.value in ("*", "/"):
            op = self.current_token.value
            self.advance()
            node = BinOpNode(node, op, self.power())
        return node

    def power(self):
        node = self.unary()
        if self.current_token.type == "Operator" and self.current_token.value == "^":
            op = self.current_token.value
            self.advance()
            node = BinOpNode(node, op, self.power())
        return node

    def unary(self):
        if self.current_token.type == "Operator" and self.current_token.value in ("+", "-"):
            op = self.current_token.value
            self.advance()
            return UnaryOpNode(op, self.unary())
        elif self.current_token.type == "IDENTIFIER" and self.current_token.value == "not":
            op = self.current_token.value
            self.advance()
            return UnaryOpNode(op, self.unary())
        return self.primary()

    def primary(self):
        token = self.current_token
        node = None

        if token.type in ("INT", "Float"):
            self.advance()
            node = NumNode(token.value)

        elif token.type == "String":
            self.advance()
            node = StringNode(token.value)

        elif token.type == "LBRACKET":
            self.advance()
            elements = []
            if self.current_token.type != "RBRACKET":
                elements.append(self.expr())
                while self.current_token.type == "COMMA":
                    self.advance()
                    elements.append(self.expr())

            if self.current_token.type != "RBRACKET":
                self.error("Liste sonunda ']' bekleniyor")
            self.advance()
            node = ListNode(elements)

        elif token.type == "IDENTIFIER":
            name = token.value
            self.advance()

            if self.current_token.type == "LPARAN":
                self.advance()
                args = []
                if self.current_token.type != "RPARAN":
                    args.append(self.expr())
                    while self.current_token.type == "COMMA":
                        self.advance()
                        args.append(self.expr())

                if self.current_token.type != "RPARAN":
                    self.error("Kapanış parantezi ')' bekleniyor")
                self.advance()
                node = FunctionCallNode(name, args)
            else:
                node = VarNode(name)

        elif token.type == "LPARAN":
            self.advance()
            node = self.expr()
            if self.current_token.type != "RPARAN":
                self.error("Kapanış parantezi ')' bekleniyor")
            self.advance()

        else:
            self.error("Sözdizimi Hatası")

        while self.current_token.type == "LBRACKET":
            self.advance()
            index_expr = self.expr()
            if self.current_token.type != "RBRACKET":
                self.error("İndeks erişimi sonunda ']' bekleniyor")
            self.advance()
            node = IndexAccessNode(node, index_expr)

        return node


# =====================================================================
# 4. INTERPRETER
# =====================================================================

class Interpreter:
    BUILTIN_FUNCTIONS = {
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "sqrt": math.sqrt,
        "abs": abs,
        "log": math.log,
        "len": len
    }

    def __init__(self, global_env, user_functions=None):
        self.global_env = global_env
        self.user_functions = user_functions if user_functions is not None else {}

    def visit(self, node, local_env=None):
        if node is None:
            return None

        current_env = local_env if local_env is not None else self.global_env

        if isinstance(node, NumNode):
            return node.value

        elif isinstance(node, StringNode):
            return node.value

        elif isinstance(node, ListNode):
            return [self.visit(elem, local_env) for elem in node.elements]

        elif isinstance(node, IndexAccessNode):
            target_list = self.visit(node.target, local_env)
            index_val = int(self.visit(node.index_expr, local_env))

            if not isinstance(target_list, list):
                raise TypeError("İndeks erişimi yalnızca listeler üzerinde yapılabilir.")
            if index_val < 0 or index_val >= len(target_list):
                raise IndexError(f"Liste indeksi sınırların dışında: {index_val}")

            return target_list[index_val]

        elif isinstance(node, IndexAssignNode):
            target_list = self.visit(node.target, local_env)
            index_val = int(self.visit(node.index_expr, local_env))
            new_val = self.visit(node.expr, local_env)

            if not isinstance(target_list, list):
                raise TypeError("İndeks ile değer ataması yalnızca listeler üzerinde yapılabilir.")
            if index_val < 0 or index_val >= len(target_list):
                raise IndexError(f"Liste indeksi sınırların dışında: {index_val}")

            target_list[index_val] = new_val
            return new_val

        elif isinstance(node, VarNode):
            if node.name == "pi":
                return math.pi
            elif node.name == "e":
                return math.e
            elif local_env is not None and node.name in local_env:
                return local_env[node.name]
            elif node.name in self.global_env:
                return self.global_env[node.name]
            else:
                raise NameError(f"Tanımsız değişken: '{node.name}'")

        elif isinstance(node, UnaryOpNode):
            val = self.visit(node.expr, local_env)
            if node.op == "-":
                return -val
            elif node.op == "+":
                return +val
            elif node.op == "not":
                return 0.0 if (val != 0.0 and val is not None) else 1.0

        elif isinstance(node, BinOpNode):
            if node.op == "and":
                left = self.visit(node.left, local_env)
                if left == 0.0 or left is None:
                    return 0.0
                right = self.visit(node.right, local_env)
                return 1.0 if (right != 0.0 and right is not None) else 0.0

            elif node.op == "or":
                left = self.visit(node.left, local_env)
                if left != 0.0 and left is not None:
                    return 1.0
                right = self.visit(node.right, local_env)
                return 1.0 if (right != 0.0 and right is not None) else 0.0

            left = self.visit(node.left, local_env)
            right = self.visit(node.right, local_env)

            if node.op == "+":
                if isinstance(left, str) or isinstance(right, str):
                    left_str = str(int(left)) if isinstance(left, float) and left.is_integer() else str(left)
                    right_str = str(int(right)) if isinstance(right, float) and right.is_integer() else str(right)
                    return left_str + right_str

            match node.op:
                case "+": return left + right
                case "-": return left - right
                case "*": return left * right
                case "/": return left / right
                case "^": return left ** right
                case "==": return 1.0 if left == right else 0.0
                case "!=": return 1.0 if left != right else 0.0
                case ">": return 1.0 if left > right else 0.0
                case "<": return 1.0 if left < right else 0.0
                case ">=": return 1.0 if left >= right else 0.0
                case "<=": return 1.0 if left <= right else 0.0

        elif isinstance(node, AssignNode):
            val = self.visit(node.expr, local_env)
            current_env[node.var_name] = val
            return val

        elif isinstance(node, FunctionDefNode):
            self.user_functions[node.name] = node
            return f"<function '{node.name}'>"

        elif isinstance(node, ReturnNode):
            val = self.visit(node.expr, local_env)
            raise ReturnException(val)

        elif isinstance(node, BreakNode):
            raise BreakException()

        elif isinstance(node, ContinueNode):
            raise ContinueException()

        elif isinstance(node, FunctionCallNode):
            func_name = node.func_name
            evaluated_args = [self.visit(arg, local_env) for arg in node.args]

            if func_name == "print":
                val = evaluated_args[0] if evaluated_args else None
                print(f"[ÇIKTI]: {val}")
                return val

            elif func_name == "input":
                prompt = evaluated_args[0] if evaluated_args else "[GİRDİ Bekleniyor]: "
                user_val = input(str(prompt))
                try:
                    return float(user_val)
                except ValueError:
                    return user_val

            elif func_name == "push":
                if len(evaluated_args) < 2:
                    raise TypeError("push() fonksiyonu 2 parametre bekler: push(liste, eleman)")
                target_list = evaluated_args[0]
                element = evaluated_args[1]

                if not isinstance(target_list, list):
                    raise TypeError("push() fonksiyonunun ilk parametresi bir liste olmalıdır.")

                target_list.append(element)
                return element

            elif func_name == "pop":
                if len(evaluated_args) < 1:
                    raise TypeError("pop() fonksiyonu en az 1 parametre bekler: pop(liste)")
                target_list = evaluated_args[0]

                if not isinstance(target_list, list):
                    raise TypeError("pop() fonksiyonunun parametresi bir liste olmalıdır.")
                if len(target_list) == 0:
                    raise IndexError("Boş bir listeden eleman çıkarılamaz (pop from empty list).")

                return target_list.pop()

            elif func_name in self.BUILTIN_FUNCTIONS:
                func = self.BUILTIN_FUNCTIONS[func_name]
                return func(evaluated_args[0])

            elif func_name in self.user_functions:
                func_def = self.user_functions[func_name]

                if len(evaluated_args) != len(func_def.params):
                    raise TypeError(f"'{func_name}' fonksiyonu {len(func_def.params)} parametre bekliyor, {len(evaluated_args)} verildi.")

                new_local_env = {}
                for param_name, arg_val in zip(func_def.params, evaluated_args):
                    new_local_env[param_name] = arg_val

                try:
                    return self.visit(func_def.body, new_local_env)
                except ReturnException as ret:
                    return ret.value

            else:
                raise NameError(f"Tanımsız fonksiyon: '{func_name}'")

        elif isinstance(node, BlockNode):
            last_val = None
            for stmt in node.statements:
                last_val = self.visit(stmt, local_env)
            return last_val

        elif isinstance(node, IfNode):
            cond_val = self.visit(node.condition, local_env)
            if cond_val != 0.0:
                return self.visit(node.then_branch, local_env)
            elif node.else_branch is not None:
                return self.visit(node.else_branch, local_env)
            return None

        elif isinstance(node, WhileNode):
            last_val = None
            while self.visit(node.condition, local_env) != 0.0:
                try:
                    last_val = self.visit(node.body, local_env)
                except BreakException:
                    break
                except ContinueException:
                    continue
            return last_val

        raise RuntimeError(f"Bilinmeyen düğüm tipi: {type(node)}")


# =====================================================================
# 5. REPL ARAYÜZÜ
# =====================================================================

def main():
    global_env = {}
    user_functions = {}
    interpreter = Interpreter(global_env, user_functions)

    if len(sys.argv) > 1:
        filename = sys.argv[1]
        try:
            with open(filename, "r", encoding="utf-8") as f:
                code = f.read()
            lexer = Lexer(code)
            parser = Parser(lexer)
            ast = parser.parse()
            if ast is not None:
                interpreter.visit(ast)
        except Exception as e:
            print(f"Hata: {e}")
        return

    print("=" * 55)
    print("  Düzeltilmiş AST Yorumlayıcısı (v12.1)")
    print("  Çıkmak için 'exit', dosya için 'run dosya.txt'")
    print("=" * 55)

    while True:
        try:
            inp = input("\n>>> ").strip()

            if not inp:
                continue

            if inp.lower() in ("exit", "q", "quit"):
                print("Yorumlayıcı kapatılıyor...")
                break

            if inp.lower().startswith("run "):
                filename = inp[4:].strip()
                try:
                    with open(filename, "r", encoding="utf-8") as f:
                        code = f.read()

                    global_env.clear()
                    user_functions.clear()

                    lexer = Lexer(code)
                    parser = Parser(lexer)
                    ast = parser.parse()

                    if ast is not None:
                        interpreter.visit(ast)
                    print(f"[{filename} başarıyla çalıştırıldı.]")
                except FileNotFoundError:
                    print(f"Hata: '{filename}' adında bir dosya bulunamadı.")
                except Exception as e:
                    print(f"Çalıştırma Hatası: {e}")
                continue

            if inp.lower() in ("vars", "hafiza"):
                print("Küresel Değişkenler:", global_env)
                print("Tanımlı Fonksiyonlar:", list(user_functions.keys()))
                continue

            if inp.lower() in ("clear", "temizle"):
                os.system('cls' if os.name == 'nt' else 'clear')
                continue

            lexer = Lexer(inp)
            parser = Parser(lexer)
            ast = parser.parse()

            if ast is not None:
                result = interpreter.visit(ast)
                if result is not None:
                    print(f"-> {result}")

        except Exception as e:
            print(f"Hata: {e}")


if __name__ == "__main__":
    main()