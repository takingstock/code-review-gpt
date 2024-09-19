import yaml
import os

class SwaggerScannerBase:
    def __init__(self, yaml_files):
        self.yaml_files = yaml_files
        self.endpoints = []
        self.scan_yaml_files()

    def scan_yaml_files(self):
        """Scans all YAML files in the directory for API endpoints."""
        for file in self.yaml_files:
                if file.endswith(('.yaml', '.yml')):
                    with open( file, 'r') as f:
                        try:
                            swagger_doc = yaml.safe_load(f)
                            self._extract_endpoints(swagger_doc)
                        except yaml.YAMLError as e:
                            print(f"Error parsing YAML file {yaml_path}: {e}")

    def _extract_endpoints(self, swagger_doc):
        """Extracts API endpoints from the parsed Swagger/OpenAPI YAML."""
        if 'paths' in swagger_doc:
            for path, methods in swagger_doc['paths'].items():
                for method, details in methods.items():
                    self.endpoints.append(path)

    def find_implementing_methods(self):
        """Abstract method to be implemented in the child classes for language-specific logic."""
        raise NotImplementedError("This method should be implemented by subclasses")

