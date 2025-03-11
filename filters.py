from typing import Dict, List, Set, Optional
from metadata import FunctionMetadata

class GraphFilter:
    """Handles filtering of nodes and relationships in the code graph."""
    
    def __init__(self):
        self.node_types = {'folder', 'file', 'function'}
        self.extension_colors = {
            '.py': '#3572A5',    # Python blue
            '.js': '#F7DF1E',    # JavaScript yellow
            '.ts': '#3178C6',    # TypeScript blue
            '.java': '#B07219',  # Java brown
            '.cpp': '#F34B7D',   # C++ pink
            '.c': '#555555',     # C gray
        }
        self.folder_color = '#4CAF50'  # Green
        
    def filter_by_type(self, nodes: Dict, node_type: str) -> Dict:
        """Filter nodes by type (folder, file, or function)."""
        if node_type not in self.node_types:
            return nodes
            
        return {
            k: v for k, v in nodes.items()
            if (node_type == 'folder' and v.get('type') == 'folder') or
               (node_type == 'file' and v.get('type') == 'file') or
               (node_type == 'function' and v.get('type') == 'function')
        }
        
    def filter_by_name(self, nodes: Dict, name_pattern: str) -> Dict:
        """Filter nodes by name pattern."""
        if not name_pattern:
            return nodes
            
        pattern = name_pattern.lower()
        return {
            k: v for k, v in nodes.items()
            if pattern in k.lower() or pattern in v.get('label', '').lower()
        }
        
    def filter_by_relationships(self, nodes: Dict, relationships: Dict,
                              selected_nodes: List[str], direction: str = 'both') -> Dict:
        """Filter nodes based on their relationships to selected nodes."""
        if not selected_nodes:
            return nodes
            
        keep_nodes = set(selected_nodes)
        
        for node_id in selected_nodes:
            if node_id in relationships:
                if direction in ('both', 'out'):
                    keep_nodes.update(relationships[node_id]['calls'])
                if direction in ('both', 'in'):
                    keep_nodes.update(relationships[node_id]['called_by'])
                    
        return {k: v for k, v in nodes.items() if k in keep_nodes}
        
    def get_node_color(self, node_type: str, file_extension: Optional[str] = None) -> str:
        """Get the color for a node based on its type and extension."""
        if node_type == 'folder':
            return self.folder_color
        elif node_type == 'file':
            return self.extension_colors.get(file_extension, '#999999')  # Default gray
        else:
            return '#2196F3'  # Function blue
            
    def apply_filters(self, nodes: Dict, relationships: Dict,
                     node_type: Optional[str] = None,
                     name_pattern: Optional[str] = None,
                     selected_nodes: Optional[List[str]] = None,
                     relationship_direction: str = 'both') -> Dict:
        """Apply all filters in sequence."""
        filtered_nodes = nodes.copy()
        
        if node_type:
            filtered_nodes = self.filter_by_type(filtered_nodes, node_type)
            
        if name_pattern:
            filtered_nodes = self.filter_by_name(filtered_nodes, name_pattern)
            
        if selected_nodes:
            filtered_nodes = self.filter_by_relationships(
                filtered_nodes, relationships, selected_nodes, relationship_direction
            )
            
        return filtered_nodes 