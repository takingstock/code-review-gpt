import os
import re
from tree_sitter import Language, Parser

# Build Tree-sitter with Python grammar
Language.build_library(
    'build/my-languages.so',
    ['vendor/tree-sitter-python']  # Path to the Python grammar
)
PY_LANGUAGE = Language('build/my-languages.so', 'python')


class PythonASTExtractor:
    def __init__(self):
        self.parser = Parser(PY_LANGUAGE)
        self.parser.set_language(PY_LANGUAGE)
        self.data_ = dict()

    def find_enclosing_function( self, node, code ):
        current_node = node
        while current_node:
            # Check if the current node is a function/method definition
            if current_node.type == 'function_definition':
                # Extract the function name
                function_name = current_node.child_by_field_name('name')
                ## get the code snippet for the method and get the first line containing the definition
                func_code     = (code[ current_node.start_byte: current_node.end_byte ].split('\n'))[0]
                return { 'func_name_': function_name.text.decode('utf-8'), 'func_defn_': func_code }
            # Move to the parent node
            current_node = current_node.parent
        return { 'func_name_': 'NA', 'func_defn_': 'NA' } 

    def extract_from_file(self, file_path):
        """Reads the Python file and parses it for AST analysis."""
        if not os.path.exists(file_path) or file_path.endswith(".py") != True:
            print(f"File {file_path} does not exist OR file is NOT a python file")
            return
        
        with open(file_path, "r") as file:
            code = file.read()
        
        self._analyze_code( code, file_path )

    def _analyze_code(self, code, file_path):
        """Analyzes the code to extract information."""
        self.tree = self.parser.parse(bytes(code, "utf8"))
        self.root_node = self.tree.root_node

        cursor = self.root_node.walk()

        def walk_tree(cursor):
            """Recursively walks through the AST using the TreeCursor."""
            node = cursor.node
            self._process_node(node, code, file_path)  # Process the current node

            # Recursively visit all child nodes
            if cursor.goto_first_child():
                while True:
                    walk_tree(cursor)
                    if not cursor.goto_next_sibling():
                        break
                cursor.goto_parent()

        walk_tree(cursor)

    def _process_node(self, node, code, file_path):
        """Identifies the node type and extracts relevant information."""
        node_type = node.type
        code_snippet = code[node.start_byte:node.end_byte]
        
        # Handle specific node types
        if node_type == 'assignment':
            self._handle_assignment(node, code, code_snippet, file_path)
        elif node_type == 'call':
            self._handle_function_call(node, code, code_snippet, file_path)
        # Add more cases for declarations, loops, etc.

    def _handle_assignment(self, node, code, code_snippet, file_path):
        """Handles assignment operations."""
        ##NOTE-> might NOT BE NEEDED
        lhs = node.child_by_field_name('left')
        rhs = node.child_by_field_name('right')

        lhs_code = code[lhs.start_byte:lhs.end_byte]
        rhs_code = code[rhs.start_byte:rhs.end_byte]
        parent_method_ = self.find_enclosing_function( node, code )

        if parent_method_["func_name_"] != 'NA':
            key_ = file_path +'#'+ parent_method_["func_name_"]

            tmp_ll_ = self.data_.get( key_, [] )

            tmp_ll_.append( { 'Enclosing_Method': parent_method_, 'Assignment': code_snippet,\
                'LHS': lhs_code, 'RHS': rhs_code, 'Index': len( tmp_ll_ ) } )

            self.data_[ key_ ] = tmp_ll_

    def _handle_function_call(self, node, code, code_snippet, file_path):
        """Handles function calls."""
        func_name_node = node.child_by_field_name('function')
        arguments = node.child_by_field_name('arguments')

        func_name = code[func_name_node.start_byte:func_name_node.end_byte]
        args_code = code[arguments.start_byte:arguments.end_byte]
        parent_method_ = self.find_enclosing_function( node, code )

        if parent_method_["func_name_"] != 'NA':
            key_ = file_path +'#'+ parent_method_["func_name_"]

            tmp_ll_ = self.data_.get( key_, [] )

            tmp_ll_.append( { 'Enclosing_Method': parent_method_, 'Function Call': code_snippet,\
                    'Function Name': func_name, 'Arguments': args_code, 'Index': len( tmp_ll_ ) } )

            self.data_[ key_ ] = tmp_ll_

# Usage
if __name__ == "__main__":
    import time, json, os
    start_ = time.time()
    file_path = "/home/ubuntu/ABHIJEET/INVOICES/REQUORDIT/DEV/flask_utils/"  # Path to the Python file to be analyzed
    #file_path = "/datadrive/EXPERIMENTS/IPRU/py_code/createJsonFeats.py"  # Path to the Python file to be analyzed
    ll_ = os.listdir( file_path )
    ll_ = [ file_path + x for x in ll_ ]

    extractor = PythonASTExtractor()

    for fnm_ in ll_:
        extractor.extract_from_file( fnm_ )

    with open('TMP_RES.json', 'w+') as fp:
        json.dump( extractor.data_, fp, indent=4 )
    
    print('DIDI=>', time.time() - start_)
