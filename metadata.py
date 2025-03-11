import ast
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

@dataclass
class FunctionMetadata:
    """Class for storing function metadata."""
    name: str
    folder_path: str
    file_path: str
    script_type: str
    docstring: Optional[str]
    parameters: List[Dict[str, str]]
    returns: Optional[str]
    line_number: int
    called_functions: List[str]
    used_classes: List[str]

@dataclass
class ClassMetadata:
    """Class for storing class metadata."""
    name: str
    folder_path: str
    file_path: str
    script_type: str
    docstring: Optional[str]
    methods: List[FunctionMetadata]

class MetadataExtractor:
    """Extracts metadata from Python source files."""
    
    def __init__(self):
        self.current_file = ""
        self.current_folder = ""
        
    def extract_type_hint(self, annotation: Optional[ast.AST]) -> str:
        """Extract type hint from AST annotation."""
        if annotation is None:
            return "Any"
        
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Subscript):
            value = self.extract_type_hint(annotation.value)
            slice_value = self.extract_type_hint(annotation.slice)
            return f"{value}[{slice_value}]"
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        elif isinstance(annotation, ast.List):
            return "List"
        elif isinstance(annotation, ast.Dict):
            return "Dict"
        else:
            return "Any"

    def extract_function_calls(self, node: ast.FunctionDef) -> List[str]:
        """Extract function calls from a function definition."""
        calls = []
        
        class FunctionCallVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name):
                    calls.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.append(node.func.attr)
                self.generic_visit(node)
                
        FunctionCallVisitor().visit(node)
        return calls

    def extract_class_usages(self, node: ast.FunctionDef) -> List[str]:
        """Extract class usages from a function definition."""
        class_usages = []
        
        class ClassUsageVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                # Check for class instantiation patterns, e.g., x = ClassName()
                if isinstance(node.func, ast.Name):
                    # Python naming convention: class names typically start with uppercase
                    if node.func.id and node.func.id[0].isupper():
                        class_usages.append(node.func.id)
                self.generic_visit(node)
                
            def visit_Name(self, node):
                # Check for direct class references
                if isinstance(node, ast.Name) and node.id and node.id[0].isupper():
                    class_usages.append(node.id)
                self.generic_visit(node)
                
        ClassUsageVisitor().visit(node)
        return list(set(class_usages))  # Remove duplicates

    def extract_function_metadata(self, node: ast.FunctionDef) -> FunctionMetadata:
        """Extract metadata from a function definition."""
        # Get docstring using ast.get_docstring instead of ast_comments
        docstring = ast.get_docstring(node) or ""
        
        # Extract parameters
        parameters = []
        for arg in node.args.args:
            param_type = self.extract_type_hint(arg.annotation)
            parameters.append({
                'name': arg.arg,
                'type': param_type
            })
            
        # Extract return type
        returns = self.extract_type_hint(node.returns)
        
        # Extract function calls
        called_functions = self.extract_function_calls(node)
        
        # Extract class usages
        used_classes = self.extract_class_usages(node)
        
        return FunctionMetadata(
            name=node.name,
            folder_path=self.current_folder,
            file_path=self.current_file,
            script_type=os.path.splitext(self.current_file)[1],
            docstring=docstring,
            parameters=parameters,
            returns=returns,
            line_number=node.lineno,
            called_functions=called_functions,
            used_classes=used_classes
        )

    def extract_class_metadata(self, node: ast.ClassDef) -> ClassMetadata:
        """Extract metadata from a class definition."""
        docstring = ast.get_docstring(node) or ""
        methods = [self.extract_function_metadata(n) for n in node.body if isinstance(n, ast.FunctionDef)]
        
        return ClassMetadata(
            name=node.name,
            folder_path=self.current_folder,
            file_path=self.current_file,
            script_type=os.path.splitext(self.current_file)[1],
            docstring=docstring,
            methods=methods
        )

    def process_file(self, file_path: str) -> Tuple[List[FunctionMetadata], List[ClassMetadata]]:
        """Process a Python file and extract metadata from all functions and classes."""
        self.current_file = file_path
        self.current_folder = os.path.dirname(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                return [], []
                
        functions = []
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(self.extract_function_metadata(node))
            elif isinstance(node, ast.ClassDef):
                classes.append(self.extract_class_metadata(node))
                
        return functions, classes 