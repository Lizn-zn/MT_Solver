from pysmt.smtlib.parser import SmtLibParser
from pysmt.shortcuts import REAL, INT, BOOL, Not, HRPrinter, BottemaPrinter
from io import StringIO
import subprocess
from warnings import warn
from src.exceptions import maple_compile_errors, FormulaParseError
from src.result import Result
from src.utils import *

class bottema_compiler:
    """ 
        The class to compile the SMT-LIB2 format statement into bottema format
    """
    def __init__(self):
        self.word_dict = {}
        
    def _reset(self):
        self.vars, self.cmds, self.funs, self.exprs, self.goals = [], [], [], [], []
    
    def declare_var(self, name, type):
        """ Declare a variable for solving """
        self.vars.append({'name': name, 'type': type})
    
    def declare_fun(self, name, input_types, output_type):
        """ Declare a function for solving """
        raise NotImplementedError('Unsupport command declare-fun')

    def define_fun(self, name, vars, rtype, expr):
        """ Define a function for solving """
        self.funs.append(f"{name} := {expr.serialize(printer=BottemaPrinter)}")

    def define_fun_rec(self, name, vars, type, expr, recur_iter=10):
        """ Define a recursive function for solving 
            In contrast to declare_fun, declare_fun_rec is defined by equation f(x) = g(f(x)) instead
        """
        raise NotImplementedError('Unsupport command define-fun')

    def parse_formula(self, cmd):
        self.cmds.append(cmd)

    def parse_objective(self, cmd, minimize=True):
        raise NotImplementedError('Unsupport command minimize/maximize')
    
    def check_sat(self):
        """ check sat 
        Note that the last cmd should be the goal
        """
        for cmd in self.cmds[:-1]: 
            self.exprs.append(cmd.serialize(printer=BottemaPrinter))
        if self.cmds[-1].is_not():
            self.goals.append(Not(self.cmds[-1]).serialize(printer=BottemaPrinter))
        else:
            raise FormulaParseError("the prove goal should be the negation form")
            
    def compile(self, statement):
        """ compile the smt-lib statement
        """
        self._reset()
        smt_parser = SmtLibParser()
        for cmd in smt_parser.get_command_generator(StringIO(statement)):
            #### Note: cmd.args[0] is fnode
            if cmd.name == "declare-fun" or cmd.name == "declare-const":
                var = cmd.args[0]
                tmp_name, tmp_type = var.symbol_name(), var.symbol_type()
                if not tmp_type.is_function_type():
                    self.declare_var(tmp_name, tmp_type)
                else:
                    func_type = cmd.args[1]
                    param_types, return_type = func_type.param_types, func_type.return_type
                    self.declare_fun(tmp_name, param_types, return_type)
            elif cmd.name == "define-fun":
                tmp_name, tmp_vars, tmp_type, tmp_expr = cmd.args
                self.define_fun(tmp_name, tmp_vars, tmp_type, tmp_expr)
            elif cmd.name == "define-fun-rec":
                tmp_name, tmp_vars, tmp_type, tmp_expr = cmd.args
                self.define_fun_rec(tmp_name, tmp_vars, tmp_type, tmp_expr)
            elif cmd.name == "assert":
                self.parse_formula(cmd.args[0])
            elif cmd.name == "minimize":
                self.parse_objective(cmd.args[0], minimize=True)
            elif cmd.name == "maximize":
                self.parse_objective(cmd.args[0], minimize=False)
            elif cmd.name == "check-sat": 
                self.check_sat()
            elif cmd.name == "get-value":
                self.target_vars = [arg for arg in cmd.args]
            elif cmd.name == "get-model":
                self.target_vars = self.vars

class bottema_solver(bottema_compiler):
    def __init__(self):
        """ hyper-parameters setting
        """
        bottema_compiler.__init__(self)
        
    def reset(self):
        self.solutions = []
    
    def solve(self, args):
        """ solve and parse the result 
        """
        exec_cmd = 'maple'
        func_cmd = ';'.join(self.funs)
        prove_cmd = f'yprove({self.goals[0]}, [{",".join(self.exprs)}])'
        exec_args = f'interface(prettyprint=0): read "./src/Bottema/bottema.mpl": {func_cmd}; {prove_cmd};'
        timeout = int(args.get("timeout", 30))
        output, error = wrap_exec(exec_cmd, exec_args, timeout)
        start_marker, end_marker = exec_args, '> quit'
        output = parse_string(output, start_marker, end_marker)
        if "The inequality holds!" in output:
            return Result.UNSAT, "no counter example exists"
        else:
            start_marker = "`output a counter example`"
            end_marker = "`The inequality does not hold.`"
            res = parse_string(output, start_marker, end_marker) 
            if res != "": 
                return Result.SAT, res
            else:   
                return Result.EXCEPT, error
        
def bottema_solve(statement, solver_name, args):
    s = bottema_solver()
    try:
        s.compile(statement) 
    except maple_compile_errors as e:
        return Result.EXCEPT, f"maple compilation failed: {e}"
    res = s.solve(args)
    return res

            