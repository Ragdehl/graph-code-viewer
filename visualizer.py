import dash
from dash import html, dcc
import dash_cytoscape as cyto
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from typing import Dict, List, Tuple
import json
from filters import GraphFilter
import colorsys
import hashlib

class GraphVisualizer:
    """Handles the interactive visualization of the code graph."""
    
    def __init__(self, functions: List, classes: List, file_info: Dict, relationships: Dict):
        self.functions = functions
        self.classes = classes
        self.file_info = file_info
        self.relationships = relationships
        self.filter_manager = GraphFilter()
        # Register the layout we'll use
        cyto.load_extra_layouts()
        self.app = self._create_app()
        
    def _create_nodes_and_edges(self, filtered_nodes: Dict = None) -> Tuple[List, List]:
        """Create nodes and edges for the graph visualization."""
        nodes = []
        edges = []
        
        # Generate a color map for files
        def get_file_color(file_path: str) -> str:
            """Generate a consistent color based on file path."""
            hash_value = int(hashlib.md5(file_path.encode()).hexdigest(), 16)
            hue = (hash_value % 1000) / 1000.0
            rgb = colorsys.hsv_to_rgb(hue, 0.7, 0.9)
            return f'rgb({int(rgb[0]*255)}, {int(rgb[1]*255)}, {int(rgb[2]*255)})'

        # Create color map for files
        file_colors = {file_path: get_file_color(file_path) 
                      for file_path in self.file_info.keys()}
        
        # Add folder nodes
        folders = set(info['folder'] for info in self.file_info.values())
        for folder in folders:
            nodes.append({
                'data': {
                    'id': f"folder:{folder}",
                    'label': folder.split('/')[-1],
                    'type': 'folder'
                },
                'classes': 'folder'
            })
            
        # Add file nodes
        for file_path, info in self.file_info.items():
            nodes.append({
                'data': {
                    'id': f"file:{file_path}",
                    'label': file_path.split('/')[-1],
                    'type': 'file',
                    'extension': info['type'],
                    'color': file_colors[file_path]
                },
                'classes': 'file'
            })
            # Connect folder to file (corrected direction)
            edges.append({
                'data': {
                    'source': f"folder:{info['folder']}",
                    'target': f"file:{file_path}",
                    'type': 'contains'
                }
            })
            
        # Add class nodes
        for cls in self.classes:
            cls_id = f"{cls.file_path}:{cls.name}"
            nodes.append({
                'data': {
                    'id': cls_id,
                    'label': cls.name,
                    'type': 'class',
                    'color': file_colors[cls.file_path],
                    'metadata': {
                        'docstring': cls.docstring,
                        'file_path': cls.file_path
                    }
                },
                'classes': 'class'
            })
            # Connect file to class (corrected direction)
            edges.append({
                'data': {
                    'source': f"file:{cls.file_path}",
                    'target': cls_id,
                    'type': 'contains'
                }
            })
            
            # Connect class to methods (corrected direction)
            for method in cls.methods:
                method_id = f"{method.file_path}:{method.name}"
                nodes.append({
                    'data': {
                        'id': method_id,
                        'label': method.name,
                        'type': 'method',
                        'color': file_colors[method.file_path],
                        'metadata': {
                            'docstring': method.docstring,
                            'parameters': method.parameters,
                            'returns': method.returns,
                            'file_path': method.file_path,
                            'line_number': method.line_number
                        }
                    },
                    'classes': 'method'
                })
                edges.append({
                    'data': {
                        'source': cls_id,
                        'target': method_id,
                        'type': 'contains'
                    }
                })
        
        # Add function nodes (standalone functions not in classes)
        for func in self.functions:
            func_id = f"{func.file_path}:{func.name}"
            nodes.append({
                'data': {
                    'id': func_id,
                    'label': func.name,
                    'type': 'function',
                    'color': file_colors[func.file_path],
                    'metadata': {
                        'docstring': func.docstring,
                        'parameters': func.parameters,
                        'returns': func.returns,
                        'file_path': func.file_path,
                        'line_number': func.line_number
                    }
                },
                'classes': 'function'
            })
            # Connect file to function (corrected direction)
            edges.append({
                'data': {
                    'source': f"file:{func.file_path}",
                    'target': func_id,
                    'type': 'contains'
                }
            })
        
        # Function call relationships (keep the original direction)
        for func_id, rels in self.relationships.items():
            source_file = func_id.split(':')[0]
            
            for called_func in rels.get('calls', set()):
                target_file = called_func.split(':')[0]
                
                # Only add the edge if the source and target are in the same file
                if source_file == target_file:
                    edges.append({
                        'data': {
                            'source': func_id,
                            'target': called_func,
                            'type': 'calls'
                        },
                        'classes': 'relationship'
                    })
            
            # Class usage relationships
            for used_class in rels.get('uses', set()):
                class_file = used_class.split(':')[0]
                
                # Only add the edge if in the same file
                if source_file == class_file:
                    edges.append({
                        'data': {
                            'source': func_id,
                            'target': used_class,
                            'type': 'uses'
                        },
                        'classes': 'uses-relationship'
                    })
        
        return nodes, edges

    def _get_folder_file_items(self):
        """Get list of folders and files for multiselection."""
        items = []
        
        # Add folders
        folders = set(info['folder'] for info in self.file_info.values())
        for folder in folders:
            folder_name = folder.split('\\')[-1] if '\\' in folder else folder.split('/')[-1]
            items.append({
                'label': f"📁 {folder_name}",
                'value': f"folder:{folder}"
            })
        
        # Add files
        for file_path in self.file_info:
            file_name = file_path.split('\\')[-1] if '\\' in file_path else file_path.split('/')[-1]
            items.append({
                'label': f"📄 {file_name}",
                'value': f"file:{file_path}"
            })
        
        return items

    def _create_app(self) -> dash.Dash:
        """Create the Dash application for visualization."""
        app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        
        nodes, edges = self._create_nodes_and_edges()
        folder_file_items = self._get_folder_file_items()
        
        app.layout = dbc.Container([
            html.H1("Code Repository Graph Viewer", className="my-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("File Explorer"),
                            html.P("Select folders and files to display:"),
                            dcc.Dropdown(
                                id='folder-file-selector',
                                options=folder_file_items,
                                value=[],  # Default to empty selection
                                multi=True,  # Enable multi-selection
                                clearable=True,
                                searchable=True,
                                placeholder="Select folders and files..."
                            )
                        ])
                    ], className="mb-4"),
                    
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Node Details"),
                            html.Div(id='node-details')
                        ])
                    ])
                ], width=3),
                
                dbc.Col([
                    cyto.Cytoscape(
                        id='graph',
                        layout={
                            'name': 'cose',
                            'padding': 50,
                            'nodeOverlap': 20,
                            'componentSpacing': 100,
                            'nodeRepulsion': 400000,
                            'idealEdgeLength': 100,
                            'edgeElasticity': 100,
                            'nestingFactor': 5,
                            'gravity': 80,
                            'numIter': 1000,
                            'initialTemp': 200,
                            'coolingFactor': 0.95,
                            'minTemp': 1.0
                        },
                        style={'width': '100%', 'height': '800px'},
                        elements=nodes + edges,
                        stylesheet=[
                            {
                                'selector': 'node',
                                'style': {
                                    'label': 'data(label)',
                                    'font-size': '12px',
                                    'text-wrap': 'wrap',
                                    'text-max-width': '100px'
                                }
                            },
                            {
                                'selector': '.folder',
                                'style': {
                                    'background-color': self.filter_manager.folder_color,
                                    'shape': 'rectangle',
                                    'width': '40px',
                                    'height': '40px'
                                }
                            },
                            {
                                'selector': '.file',
                                'style': {
                                    'background-color': 'data(color)',
                                    'shape': 'diamond',
                                    'width': '30px',
                                    'height': '30px'
                                }
                            },
                            {
                                'selector': '.function',
                                'style': {
                                    'background-color': 'data(color)',
                                    'shape': 'ellipse',
                                    'width': '25px',
                                    'height': '25px'
                                }
                            },
                            {
                                'selector': '.method',
                                'style': {
                                    'background-color': 'data(color)',
                                    'shape': 'ellipse',
                                    'width': '20px',
                                    'height': '20px',
                                    'border-width': '1px',
                                    'border-color': '#000'
                                }
                            },
                            {
                                'selector': '.class',
                                'style': {
                                    'background-color': 'data(color)',
                                    'shape': 'round-rectangle',
                                    'width': '35px',
                                    'height': '35px'
                                }
                            },
                            {
                                'selector': '.uses-relationship',
                                'style': {
                                    'curve-style': 'bezier',
                                    'target-arrow-shape': 'diamond',
                                    'line-color': '#0077cc',
                                    'target-arrow-color': '#0077cc',
                                    'line-style': 'dashed',
                                    'opacity': 0.7
                                }
                            },
                            {
                                'selector': 'edge',
                                'style': {
                                    'curve-style': 'bezier',  # Simpler edge style
                                    'target-arrow-shape': 'triangle',
                                    'arrow-scale': 1,
                                    'line-color': '#666',
                                    'target-arrow-color': '#666',
                                    'opacity': 0.7,
                                    'width': 2
                                }
                            },
                            {
                                'selector': '.relationship',
                                'style': {
                                    'curve-style': 'bezier',
                                    'target-arrow-shape': 'triangle',
                                    'line-color': '#666',
                                    'target-arrow-color': '#666',
                                    'opacity': 0.7
                                }
                            },
                            {
                                'selector': '.highlighted',
                                'style': {
                                    'line-color': '#f00',
                                    'target-arrow-color': '#f00',
                                    'opacity': 1,
                                    'width': 3
                                }
                            },
                            {
                                'selector': ':selected',
                                'style': {
                                    'border-width': 3,
                                    'border-color': '#333'
                                }
                            }
                        ],
                        # Add zoom and pan settings
                        userZoomingEnabled=True,
                        userPanningEnabled=True,
                        zoomingEnabled=True,
                        minZoom=0.1,
                        maxZoom=2.0,
                        zoom=1.0,
                        boxSelectionEnabled=True,
                        autounselectify=False
                    )
                ], width=9)
            ])
        ], fluid=True)
        
        self._setup_callbacks(app)
        return app
        
    def _setup_callbacks(self, app: dash.Dash):
        """Set up the interactive callbacks."""
        
        @app.callback(
            Output('graph', 'elements'),
            [Input('folder-file-selector', 'value')]
        )
        def update_graph(selected_items):
            try:
                # Get all nodes and edges
                all_nodes, all_edges = self._create_nodes_and_edges()
                
                # If no selections, show everything
                if not selected_items:
                    return all_nodes + all_edges
                
                # Separate selected folders and files
                selected_folders = [item for item in selected_items if item.startswith('folder:')]
                selected_files = [item for item in selected_items if item.startswith('file:')]
                
                # Keep track of nodes to display
                keep_nodes = set()
                
                # Always include the selected folders and files
                keep_nodes.update(selected_folders)
                keep_nodes.update(selected_files)
                
                # For each selected folder, add all its contained files
                for edge in all_edges:
                    if edge['data']['type'] == 'contains' and edge['data']['source'] in selected_folders:
                        keep_nodes.add(edge['data']['target'])
                
                # For each selected file, add all its contained classes and functions
                file_content_nodes = set()
                processed_files = set(selected_files)
                
                # Recursively process the hierarchy
                while processed_files:
                    current_file = processed_files.pop()
                    
                    # Find all nodes contained in this file
                    for edge in all_edges:
                        if edge['data']['source'] == current_file and edge['data']['type'] == 'contains':
                            target = edge['data']['target']
                            file_content_nodes.add(target)
                            
                            # If target is a class, also add its methods
                            for class_edge in all_edges:
                                if class_edge['data']['source'] == target and class_edge['data']['type'] == 'contains':
                                    file_content_nodes.add(class_edge['data']['target'])
                
                # Add all content nodes to our keep set
                keep_nodes.update(file_content_nodes)
                
                # Filter nodes and edges
                filtered_nodes = [n for n in all_nodes if n['data']['id'] in keep_nodes]
                filtered_edges = [e for e in all_edges if 
                                (e['data']['source'] in keep_nodes and e['data']['target'] in keep_nodes)]
                
                return filtered_nodes + filtered_edges
                
            except Exception as e:
                print(f"Error in update_graph: {str(e)}")
                return dash.no_update
        
        @app.callback(
            Output('node-details', 'children'),
            [Input('graph', 'tapNodeData')]
        )
        def display_node_data(node_data):
            if not node_data:
                return "Click a node to see details"
            
            try:
                if node_data['type'] == 'function' or node_data['type'] == 'method':
                    metadata = node_data['metadata']
                    return html.Div([
                        html.H5(node_data['label']),
                        html.P(f"Type: {node_data['type'].capitalize()}"),
                        html.P(f"File: {metadata['file_path']}"),
                        html.P(f"Line: {metadata['line_number']}"),
                        html.H6("Docstring:"),
                        html.P(metadata['docstring'] or "No docstring"),
                        html.H6("Parameters:"),
                        html.Ul([
                            html.Li(f"{param['name']}: {param['type']}")
                            for param in metadata['parameters']
                        ]),
                        html.H6("Returns:"),
                        html.P(metadata['returns'])
                    ])
                elif node_data['type'] == 'class':
                    metadata = node_data['metadata']
                    return html.Div([
                        html.H5(node_data['label']),
                        html.P(f"Type: Class"),
                        html.P(f"File: {metadata['file_path']}"),
                        html.H6("Docstring:"),
                        html.P(metadata['docstring'] or "No docstring")
                    ])
                else:
                    return html.Div([
                        html.H5(node_data['label']),
                        html.P(f"Type: {node_data['type'].capitalize()}")
                    ])
            except Exception as e:
                print(f"Error in display_node_data: {str(e)}")
                return "Error displaying node details"
        
        # Add callback for dynamic layout updates
        @app.callback(
            Output('graph', 'layout'),
            [Input('graph', 'mouseoverNodeData')]
        )
        def update_layout(node_data):
            """Update layout parameters when hovering over nodes."""
            if node_data:
                return {
                    'name': 'cola',
                    'nodeSpacing': 100,
                    'edgeLength': 200,
                    'padding': 50,
                    'animate': True,
                    'maxSimulationTime': 3000,
                    'fit': False,  # Don't reset view when updating
                    'infinite': True,
                    'springLength': 200,
                    'springCoeff': 0.0008,
                    'gravity': 1,
                    'dragCoeff': 0.02,
                    'avoidOverlap': True,
                    'refresh': 1
                }
            return dash.no_update
        
    def run_server(self, port: int = 8050, debug: bool = True):
        """Run the visualization server."""
        self.app.run_server(port=port, debug=debug) 