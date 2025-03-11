import os
from typing import Dict, List, Set, Tuple
from pathlib import Path
import git
from joblib import Parallel, delayed
from tqdm import tqdm
from metadata import MetadataExtractor, FunctionMetadata, ClassMetadata

class RepositoryScraper:
    """Scrapes a repository to extract code structure and relationships."""
    
    def __init__(self, repo_path: str, workers: int = 4):
        self.repo_path = Path(repo_path)
        self.workers = workers
        self.metadata_extractor = MetadataExtractor()
        self.supported_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c'}
        
    def is_valid_file(self, file_path: str) -> bool:
        """Check if file should be processed."""
        if not os.path.isfile(file_path):
            return False
            
        extension = os.path.splitext(file_path)[1].lower()
        if extension not in self.supported_extensions:
            return False
            
        # Skip virtual environments and build directories
        skip_patterns = {'venv', 'node_modules', '__pycache__', 'build', 'dist'}
        return not any(pattern in file_path for pattern in skip_patterns)
        
    def get_all_files(self) -> List[str]:
        """Get all valid files in the repository."""
        files = []
        for root, _, filenames in os.walk(self.repo_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                if self.is_valid_file(file_path):
                    files.append(file_path)
        return files
        
    def process_file(self, file_path: str) -> Tuple[List[FunctionMetadata], List[ClassMetadata], Dict]:
        """Process a single file and extract its metadata."""
        try:
            functions, classes = self.metadata_extractor.process_file(file_path)
            file_info = {
                'path': file_path,
                'type': os.path.splitext(file_path)[1],
                'folder': os.path.dirname(file_path)
            }
            return functions, classes, file_info
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            return [], [], {}
            
    def extract_relationships(self, functions: List[FunctionMetadata], classes: List[ClassMetadata]) -> Dict:
        """Extract relationships between functions and classes."""
        relationships = {}
        
        # Create a map of class names to their IDs for easy lookup
        class_name_map = {}
        for cls in classes:
            cls_id = f"{cls.file_path}:{cls.name}"
            if cls.name not in class_name_map:
                class_name_map[cls.name] = []
            class_name_map[cls.name].append(cls_id)
        
        # Process classes
        for cls in classes:
            cls_id = f"{cls.file_path}:{cls.name}"
            relationships[cls_id] = {'contains': set(), 'calls': set(), 'called_by': set(), 'uses': set(), 'used_by': set()}
            
            for method in cls.methods:
                method_id = f"{method.file_path}:{method.name}"
                relationships[cls_id]['contains'].add(method_id)
                relationships[method_id] = {'calls': set(), 'called_by': set(), 'uses': set(), 'used_by': set()}
        
        # Initialize relationships for standalone functions
        for func in functions:
            func_id = f"{func.file_path}:{func.name}"
            if func_id not in relationships:
                relationships[func_id] = {'calls': set(), 'called_by': set(), 'uses': set(), 'used_by': set()}
        
        # Process function calls
        for func in functions:
            func_id = f"{func.file_path}:{func.name}"
            
            # Handle function calls
            for called_name in func.called_functions:
                same_file_call = f"{func.file_path}:{called_name}"
                if same_file_call in relationships:
                    relationships[func_id]['calls'].add(same_file_call)
                    relationships[same_file_call]['called_by'].add(func_id)
            
            # Handle class usages
            for used_class in func.used_classes:
                # Check if the class exists in the same file first
                same_file_class = f"{func.file_path}:{used_class}"
                if same_file_class in relationships:
                    relationships[func_id]['uses'].add(same_file_class)
                    relationships[same_file_class]['used_by'].add(func_id)
                # Then check across all files
                elif used_class in class_name_map:
                    for class_id in class_name_map[used_class]:
                        relationships[func_id]['uses'].add(class_id)
                        relationships[class_id]['used_by'].add(func_id)
        
        # Also process class methods
        for cls in classes:
            for method in cls.methods:
                method_id = f"{method.file_path}:{method.name}"
                
                # Handle function calls from methods
                for called_name in method.called_functions:
                    same_file_call = f"{method.file_path}:{called_name}"
                    if same_file_call in relationships:
                        relationships[method_id]['calls'].add(same_file_call)
                        relationships[same_file_call]['called_by'].add(method_id)
                
                # Handle class usages from methods
                for used_class in method.used_classes:
                    # Check if the class exists in the same file first
                    same_file_class = f"{method.file_path}:{used_class}"
                    if same_file_class in relationships:
                        relationships[method_id]['uses'].add(same_file_class)
                        relationships[same_file_class]['used_by'].add(method_id)
                    # Then check across all files
                    elif used_class in class_name_map:
                        for class_id in class_name_map[used_class]:
                            relationships[method_id]['uses'].add(class_id)
                            relationships[class_id]['used_by'].add(method_id)
        
        return relationships
        
    def scan_repository(self) -> Tuple[List[FunctionMetadata], List[ClassMetadata], Dict, Dict]:
        """Scan the repository and extract all metadata and relationships."""
        print("Scanning repository...")
        files = self.get_all_files()
        
        # Process files in parallel
        results = Parallel(n_jobs=self.workers)(
            delayed(self.process_file)(f) for f in tqdm(files)
        )
        
        # Combine results
        all_functions = []
        all_classes = []
        file_info = {}
        for functions, classes, info in results:
            if info:
                file_info[info['path']] = info
            all_functions.extend(functions)
            all_classes.extend(classes)
            
        # Extract relationships
        relationships = self.extract_relationships(all_functions, all_classes)
        
        return all_functions, all_classes, file_info, relationships 