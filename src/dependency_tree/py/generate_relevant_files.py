import os
import json
import shutil

class FindRelevantFiles:
    def __init__(self, language_extension, swagger_extension, codebase_dir='.', temp_dir='./tmp/'):
        self.language_extension = language_extension
        self.swagger_extension  = swagger_extension

        self.temp_dir = temp_dir
        self.codebase_dir = codebase_dir
        self.file_list, self.yaml_list = [], []

        self.discover_files()
        self.discover_files_yml()

    def discover_files(self):
        """Find all files with the specified language extension."""
        for root, dirs, files in os.walk(self.codebase_dir):
            for file in files:
                if file.endswith( self.language_extension ):
                    file_path = os.path.join(root, file)
                    self.file_list.append(file_path)

    def discover_files_yml(self):
        """Find all files with the yaml extension."""
        for root, dirs, files in os.walk(self.codebase_dir):
            for file in files:
                if file.endswith( self.swagger_extension ):
                    file_path = os.path.join(root, file)
                    self.yaml_list.append(file_path)

    def create_temp_structure(self):
        """Create a temp folder structure and copy discovered files into it."""
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

        for file_path in self.file_list:
            # Create temp folder structure based on file type
            temp_file_path = os.path.join(self.temp_dir, os.path.basename(file_path))
            shutil.copy( file_path, temp_file_path )

    def returnFiles(self):
        return { 'lang_files': self.file_list, 'swagger_files': self.yaml_list }

if __name__ == "__main__":

    finder_ = FindRelevantFiles( language_extension='.py', swagger_extension='.yml' )
    print( finder_.returnFiles() )
