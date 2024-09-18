from base_swagger_scanner import SwaggerScannerBase
from python_extractor     import PythonASTExtractor

import os, re

class PythonAPIImplementationDetails(SwaggerScannerBase):
    def __init__( self, yaml_files, code_files, py_data_ ):
        super().__init__( yaml_files ) # init base class to generate endpoint :: used in end_point_found
        self.code_files = code_files
        self.api_endpoints_ = dict()
        self.py_data_ = py_data_
        self.route_pattern = re.compile(r'@(app\.route\(\s*["\'](.*?)["\'])')
        self.def_pattern = re.compile(r'def\s+([a-zA-Z_]\w*)\s*\(')  # Method definition pattern

    def find_api_defn( self, ln_idx, py_data_ ):
        ## intention is to find out the first instance of Line["Enclosing_Method"]["func_name_"] != "NA"
        ## so we look for the first line that shows up immediately after API declaration 
        for _key_, line_dict_ in py_data_.items():
            if line_dict_["Index"] <= ln_idx: continue

            if line_dict_["Enclosing_Method"]["func_name_"] != "NA":
                return line_dict_["Enclosing_Method"]["func_name_"]

        return None

    def find_implementing_methods(self):
        """Scans Python code files to find methods implementing the extracted API endpoints."""
        for code_file_ in self.code_files:
            if code_file_.endswith(".py") != True: continue

            with open( code_file_, 'r') as f:
                lines = f.readlines()
            
            found_api = None
            for i, line in enumerate(lines):
                # Check if the line contains an API route from the list
                route_match = self.route_pattern.search(line) 
                # If an API route is found, look for the next 'def' statement (method definition)
                if route_match:
                    found_api = route_match.group(1)
                    
                    if found_api == None: continue

                    found_ = None

                    for ep in self.endpoints:
                        if ep in found_api or found_api in ep:
                            found_ = ep
                            break

                    if found_:
                        print('BB GUN=>', ep, found_api)

                        for j in range(i + 1, len(lines)):
                            def_match = self.def_pattern.search(lines[j])
                            if def_match:
                                method_name = def_match.group(1)
                                key_ = code_file_ + '#' + method_name
                                self.api_endpoints_[ key_ ] = ep

                                found_api = None  # Reset to search for another API
                                break            
