from . import vm_error
from . import vm_stack
from . import vm_address_space
from . import vm_array
import re
import time

__all__ = ["run"]

time_flag = False

# ==============================
#     バーチャルマシン実行
# ==============================
def run(text):
    start_time = time.time()
    virtual_machine = VirtualMachine(text, time_flag)
    virtual_machine.run()


# ==============================
#    バーチャルマシン内部処理
# ==============================
class VirtualMachine:

    # ===== 初期化 =====
    def __init__(self, text, time_flag):
        self.time_flag = time_flag
        self.start_time = time.time()
        self.lines = text.split("\n") # 改行区切りのリスト
        self.progmem = self._parseLines(self.lines) # パース済み命令リスト
        self.data_stack = vm_stack.Stack() # スタック
        self.return_stack = vm_stack.Stack() # リターンスタック

        self.pc = -1 # プログラムカウンタ
        self.local_area_stack = vm_stack.Stack() # ローカル変数領域のスタック
        self.local_area = vm_address_space.AddressSpace() # ローカル変数領域
        self.global_area = vm_address_space.AddressSpace() # グローバル変数領域

    
    # ===== 実行 =====
    def run(self):
        self.check_syntax()

        while True:
            # プログラムカウンタを進める
            self.pc+=1

            if self.pc >= len(self.progmem):
                 vm_error.index_error_pc(self.pc + 1)
            
            operand = self.progmem[self.pc]["operand"]
            opcode = self.progmem[self.pc]["opcode"]
            try:
                # オペランドに応じて実行
                match operand:
                    case "":
                        pass
                    case "push_int":
                        self.cmd_push_int(opcode)
                    case "push_float":
                        self.cmd_push_float(opcode)
                    case "push_char":
                        self.cmd_push_char(opcode)
                    case "add":
                        self.cmd_add()
                    case "sub":
                        self.cmd_sub()
                    case "mul":
                        self.cmd_mul()
                    case "div":
                        self.cmd_div()
                    case "dup":
                        self.cmd_dup()
                    case "store_global":
                        self.cmd_store_global(opcode)
                    case "load_global":
                        self.cmd_load_global(opcode)
                    case "free_global":
                        self.cmd_free_global(opcode)
                    case "store_local":
                        self.cmd_store_local(opcode)
                    case "load_local":
                        self.cmd_load_local(opcode)
                    case "free_local":
                        self.cmd_free_local(opcode)
                    case "new_array_int":
                        self.cmd_new_array_int(opcode)
                    case "new_array_float":
                        self.cmd_new_array_float(opcode)
                    case "new_array_char":
                        self.cmd_new_array_char(opcode)
                    case "store_local_array":
                        self.cmd_store_local_array(opcode)
                    case "store_global_array":
                        self.cmd_store_global_array(opcode)
                    case "load_local_array":
                        self.cmd_load_local_array(opcode)
                    case "load_global_array":
                        self.cmd_load_global_array(opcode)
                    case "print":
                        self.cmd_print()
                    case "print_char":
                        self.cmd_print_char()
                    case "if_equal":
                        self.cmd_if_equal(opcode)
                    case "if_greater":
                        self.cmd_if_greater(opcode)
                    case "if_less":
                        self.cmd_if_less(opcode)
                    case "jump":
                        self.cmd_jump(opcode)
                    case "call":
                        self.cmd_call(opcode)
                    case "exit":
                        self.cmd_exit()
                    case _:
                        raise vm_error.Error("ERROR_UNDEFINED_OPCODE")
            except vm_error.Error as e:
                n_line = self.pc + 1       # 行番号
                code = self.lines[self.pc] # エラーが発生したコード
                match e.args[0]:
                    case "ERROR_POP_FROM_EMPTY_STACK":
                        vm_error.index_error_pop(n_line, code)
                    case "ERROR_UNDEFINED_OPCODE":
                        vm_error.syntax_error_undefined_opcode(n_line, code)
                    case "ERROR_MISMATCHING_ARRAY_TYPE":
                        vm_error.syntax_error_mismatching_array_type(n_line, code)
                    case "ERROR_UNDEFINED_VAR":
                        vm_error.syntax_error_undefined_var(n_line, code)
                    case _:
                        vm_error.unknown_error(n_line, code)
    
    # ===== 構文解析 =====
    def _parseLines(self, lines):
        result = []
        if lines[-1] == "":
            lines = lines[:-1]

        for line in lines:
            line = re.sub(r"#.*","", line) # コメント除去
            data = line.split()

            operand = data[0] if len(data) else "" # オペランドがあれば取得
            opcode = [float(x) for x in data[1:] if x != ''] # オペコードがあれば取得
            result.append({"operand":operand, "opcode":opcode})
        return result
    
    def check_syntax(self):
        opcode_with_operand = [
            "push_int",
            "push_float",
            "push_char",
            "store_global",
            "load_global",
            "free_global",
            "store_local",
            "load_local",
            "free_local",
            "new_array_int",
            "new_array_float",
            "new_array_char",
            "store_local_array",
            "store_global_array",
            "load_local_array",
            "load_global_array",
            "if_equal",
            "if_greater",
            "if_less",
            "jump",
            "call"
        ]
        for i, line in enumerate(self.progmem):
            operand = line["operand"]
            opcode = line["opcode"]

            if operand in opcode_with_operand:
                if len(opcode) == 0:
                    code = self.lines[i]
                    vm_error.syntax_error_missing_operand(i+1, code)


    # ==============================
    #          コマンド
    # ==============================
    def cmd_push_int(self, opcode):
        self.data_stack.push(int(opcode[0]))
    
    def cmd_push_float(self, opcode):
        self.data_stack.push(float(opcode[0]))
    
    def cmd_push_char(self, opcode):
        self.data_stack.push(chr(int(opcode[0])))
    
    def cmd_new_array_int(self, opcode):
        self.data_stack.push(vm_array.Array(int, int(opcode[0])))
    
    def cmd_new_array_float(self, opcode):
        self.data_stack.push(vm_array.Array(float, int(opcode[0])))
    
    def cmd_new_array_char(self, opcode):
        self.data_stack.push(vm_array.Array(str, int(opcode[0])))
    
    def cmd_store_global_array(self, opcode):
        name = opcode[0]
        index = self.data_stack.pop()
        value = self.data_stack.pop()

        array = self.global_area.load(name)
        array.store(index, value)
    
    def cmd_store_local_array(self, opcode):
        name = opcode[0]
        index = self.data_stack.pop()
        value = self.data_stack.pop()
        
        array = self.local_area.load(name)
        array.store(index, value)
    
    def cmd_load_global_array(self, opcode):
        name = opcode[0]
        index = self.data_stack.pop()

        array = self.global_area.load(name)
        value = array.load(index)
        self.data_stack.push(value)
    
    def cmd_load_local_array(self, opcode):
        name = opcode[0]
        index = self.data_stack.pop()
        
        array = self.local_area.load(name)
        value = array.load(index)
        self.data_stack.push(value)
    
    def cmd_store_global(self, opcode):
        name = opcode[0]
        value = self.data_stack.pop()
        self.global_area.store(name, value)
    
    def cmd_load_global(self, opcode):
        name = opcode[0]
        value = self.global_area.load(name)
        self.data_stack.push(value)
    
    def cmd_store_local(self, opcode):
        name = opcode[0]
        value = self.data_stack.pop()
        self.local_area.store(name, value)
    
    def cmd_load_local(self, opcode):
        name = opcode[0]
        value = self.local_area.load(name)
        self.data_stack.push(value)
    
    def cmd_free_global(self, opcode):
        name = opcode[0]
        self.global_area.free(name)
    
    def cmd_free_local(self, opcode):
        name = opcode[0]
        self.local_area.free(name)
    
    def cmd_add(self):
        x = self.data_stack.pop()
        y = self.data_stack.pop()
        self.data_stack.push(x + y)
    
    def cmd_sub(self):
        x = self.data_stack.pop()
        y = self.data_stack.pop()
        self.data_stack.push(x - y)
    
    def cmd_mul(self):
        x = self.data_stack.pop()
        y = self.data_stack.pop()
        self.data_stack.push(x * y)

    def cmd_div(self):
        x = self.data_stack.pop()
        y = self.data_stack.pop()
        self.data_stack.push(x / y)
    
    def cmd_dup(self):
        x = self.data_stack.pop()
        self.data_stack.push(x)
        self.data_stack.push(x)
    
    def cmd_if_equal(self, opcode):
        x = self.data_stack.pop()
        y = self.data_stack.pop()
        if x == y:
            self.pc = int(opcode[0]) -2
    
    def cmd_if_greater(self, opcode):
        x = self.data_stack.pop()
        y = self.data_stack.pop()
        if x > y:
            self.pc = int(opcode[0]) -2
    
    def cmd_if_less(self, opcode):
        x = self.data_stack.pop()
        y = self.data_stack.pop()
        if x < y:
            self.pc = int(opcode[0]) -2
    
    def cmd_jump(self, opcode):
        self.pc = int(opcode[0]) -2
    
    def cmd_print(self):
        x = self.data_stack.pop()
        print(x)
    
    def cmd_print_char(self):
        x = self.data_stack.pop()
        print(chr(int(x)), end="")
    
    def cmd_call(self, opcode):
        # メモリ領域確保
        self.local_area_stack.push(self.local_area)
        self.local_area = vm_address_space.AddressSpace()
        # プログラムカウンタ変更
        self.return_stack.push(self.pc)
        self.pc = int(opcode[0]) -2
    
    def cmd_exit(self):
        if self.return_stack.is_empty():
            if self.time_flag:
                print("time: " + str(time.time() - self.start_time))
            exit(0)
        # 呼び出し前のメモリ領域に戻す
        self.local_area = self.local_area_stack.pop()
        # プログラムカウンタを戻す
        self.pc = self.return_stack.pop()