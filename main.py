import argparse
import os
import json
from pathlib import Path
from scraper import RepositoryScraper
from visualizer import GraphVisualizer
from metadata import FunctionMetadata, ClassMetadata

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Code Repository Graph Viewer - Visualize function relationships in code repositories"
    )
    parser.add_argument(
        "--repo-path",
        type=str,
        required=True,
        help="Path to the repository to analyze"
    )
    parser.add_argument(
        "--cache",
        type=bool,
        default=True,
        help="Enable caching of analysis results"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers for analysis"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8050,
        help="Port for the visualization server"
    )
    return parser.parse_args()

def load_cache(repo_path: str) -> tuple:
    """Load cached analysis results if they exist."""
    cache_file = Path(repo_path) / ".code_graph_cache.json"
    try:
        if cache_file.exists() and cache_file.stat().st_size > 0:
            with open(cache_file, 'r') as f:
                cache = json.load(f)
                
            # Convert function dictionaries back to FunctionMetadata objects
            functions = [
                FunctionMetadata(
                    name=f['name'],
                    folder_path=f['folder_path'],
                    file_path=f['file_path'],
                    script_type=f['script_type'],
                    docstring=f['docstring'],
                    parameters=f['parameters'],
                    returns=f['returns'],
                    line_number=f['line_number'],
                    called_functions=f['called_functions'],
                    used_classes=f['used_classes']
                )
                for f in cache['functions']
            ]
            
            # Convert class dictionaries back to ClassMetadata objects
            classes = [
                ClassMetadata(
                    name=c['name'],
                    folder_path=c['folder_path'],
                    file_path=c['file_path'],
                    script_type=c['script_type'],
                    docstring=c['docstring'],
                    methods=[
                        FunctionMetadata(
                            name=m['name'],
                            folder_path=m['folder_path'],
                            file_path=m['file_path'],
                            script_type=m['script_type'],
                            docstring=m['docstring'],
                            parameters=m['parameters'],
                            returns=m['returns'],
                            line_number=m['line_number'],
                            called_functions=m['called_functions'],
                            used_classes=m['used_classes']
                        )
                        for m in c['methods']
                    ]
                )
                for c in cache['classes']
            ]
            
            # Convert relationship lists back to sets
            relationships = {}
            for func_id, rel_dict in cache['relationships'].items():
                relationships[func_id] = {
                    rel_type: set(rel_list) for rel_type, rel_list in rel_dict.items()
                }
            
            return functions, classes, cache['file_info'], relationships
    except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
        print(f"Cache loading failed: {str(e)}")
    return None, None, None, None

def save_cache(repo_path: str, functions: list, classes: list, file_info: dict, relationships: dict):
    """Save analysis results to cache."""
    cache_file = Path(repo_path) / ".code_graph_cache.json"
    
    # Convert FunctionMetadata objects to dictionaries
    functions_dict = [
        {
            'name': f.name,
            'folder_path': f.folder_path,
            'file_path': f.file_path,
            'script_type': f.script_type,
            'docstring': f.docstring,
            'parameters': f.parameters,
            'returns': f.returns,
            'line_number': f.line_number,
            'called_functions': f.called_functions,
            'used_classes': f.used_classes
        }
        for f in functions
    ]
    
    # Convert ClassMetadata objects to dictionaries
    classes_dict = [
        {
            'name': c.name,
            'folder_path': c.folder_path,
            'file_path': c.file_path,
            'script_type': c.script_type,
            'docstring': c.docstring,
            'methods': [
                {
                    'name': m.name,
                    'folder_path': m.folder_path,
                    'file_path': m.file_path,
                    'script_type': m.script_type,
                    'docstring': m.docstring,
                    'parameters': m.parameters,
                    'returns': m.returns,
                    'line_number': m.line_number,
                    'called_functions': m.called_functions,
                    'used_classes': m.used_classes
                }
                for m in c.methods
            ]
        }
        for c in classes
    ]
    
    # Convert sets to lists in relationships
    serializable_relationships = {}
    for func_id, rel_dict in relationships.items():
        serializable_relationships[func_id] = {
            rel_type: list(rel_set) for rel_type, rel_set in rel_dict.items()
        }
    
    cache = {
        'functions': functions_dict,
        'classes': classes_dict,
        'file_info': file_info,
        'relationships': serializable_relationships
    }
    
    try:
        with open(cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
        print(f"Cache saved successfully to {cache_file}")
    except Exception as e:
        print(f"Failed to save cache: {str(e)}")

def main():
    """Main entry point for the application."""
    args = parse_args()
    
    # Validate repository path
    repo_path = os.path.abspath(args.repo_path)
    if not os.path.exists(repo_path):
        print(f"Error: Repository path '{repo_path}' does not exist")
        return 1
        
    # Try to load from cache first
    functions = classes = file_info = relationships = None
    if args.cache:
        print("Attempting to load from cache...")
        functions, classes, file_info, relationships = load_cache(repo_path)
        
    # If cache loading failed or cache is disabled, analyze repository
    if not all((functions, classes, file_info, relationships)):
        print("Analyzing repository...")
        scraper = RepositoryScraper(repo_path, workers=args.workers)
        functions, classes, file_info, relationships = scraper.scan_repository()
        
        if args.cache:
            print("Saving results to cache...")
            save_cache(repo_path, functions, classes, file_info, relationships)
    else:
        print("Successfully loaded from cache")
        
    # Create and run the visualization
    print(f"Starting visualization server on port {args.port}...")
    visualizer = GraphVisualizer(functions, classes, file_info, relationships)
    visualizer.run_server(port=args.port)
    
if __name__ == "__main__":
    main() 