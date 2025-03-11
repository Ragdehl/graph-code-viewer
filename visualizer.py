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
            # Connect file to folder
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
            # Connect class to file
            edges.append({
                'data': {
                    'source': f"file:{cls.file_path}",
                    'target': cls_id,
                    'type': 'contains'
                }
            })
            
            # Connect methods to class
            for method in cls.methods:
                method_id = f"{method.file_path}:{method.name}"
                edges.append({
                    'data': {
                        'source': cls_id,
                        'target': method_id,
                        'type': 'contains'
                    }
                })
        
        # Add function nodes
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
            # Connect function to file
            edges.append({
                'data': {
                    'source': f"file:{func.file_path}",
                    'target': func_id,
                    'type': 'contains'
                }
            })
            
        # Add relationship edges
        for func_id, rels in self.relationships.items():
            # Add function call relationships
            for called_func in rels.get('calls', set()):
                edges.append({
                    'data': {
                        'source': func_id,
                        'target': called_func,
                        'type': 'calls'
                    },
                    'classes': 'relationship'
                })
            
            # Add class usage relationships
            for used_class in rels.get('uses', set()):
                edges.append({
                    'data': {
                        'source': func_id,
                        'target': used_class,
                        'type': 'uses'
                    },
                    'classes': 'uses-relationship'
                })
        
        return nodes, edges

    def _get_searchable_items(self):
        """Get list of searchable items for autocomplete."""
        items = []
        # Add functions
        for func in self.functions:
            items.append({
                'label': f"Function: {func.name}",
                'value': f"{func.file_path}:{func.name}"
            })
        # Add files
        for file_path in self.file_info:
            items.append({
                'label': f"File: {file_path.split('/')[-1]}",
                'value': f"file:{file_path}"
            })
        # Add folders
        folders = set(info['folder'] for info in self.file_info.values())
        for folder in folders:
            items.append({
                'label': f"Folder: {folder.split('/')[-1]}",
                'value': f"folder:{folder}"
            })
        return items

    def _create_app(self) -> dash.Dash:
        """Create the Dash application for visualization."""
        app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        
        nodes, edges = self._create_nodes_and_edges()
        searchable_items = self._get_searchable_items()
        
        app.layout = dbc.Container([
            html.H1("Code Repository Graph Viewer", className="my-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Filters"),
                            dbc.Form([
                                dbc.Label("Node Type"),
                                dcc.Dropdown(
                                    id='node-type-filter',
                                    options=[
                                        {'label': 'All', 'value': 'all'},
                                        {'label': 'Folders', 'value': 'folder'},
                                        {'label': 'Files', 'value': 'file'},
                                        {'label': 'Functions', 'value': 'function'},
                                        {'label': 'Classes', 'value': 'class'}
                                    ],
                                    value='all',
                                    clearable=False
                                ),
                                html.Br(),
                                dbc.Label("Search"),
                                dcc.Dropdown(
                                    id='search-filter',
                                    options=searchable_items,
                                    value=None,
                                    clearable=True,
                                    searchable=True,
                                    placeholder="Type to search..."
                                ),
                                html.Br(),
                                dbc.Label("Relationship Direction"),
                                dcc.Dropdown(
                                    id='relationship-direction',
                                    options=[
                                        {'label': 'Both', 'value': 'both'},
                                        {'label': 'Incoming', 'value': 'in'},
                                        {'label': 'Outgoing', 'value': 'out'}
                                    ],
                                    value='both',
                                    clearable=False
                                )
                            ])
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
                            'name': 'cose',  # Using simpler cose layout
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
                        zoom=1.0
                    )
                ], width=9)
            ])
        ], fluid=True)
        
        self._setup_callbacks(app)
        return app
        
    def _setup_callbacks(self, app: dash.Dash):
        """Set up the interactive callbacks."""
        
        @app.callback(
            [Output('graph', 'elements'),
             Output('search-filter', 'options')],
            [Input('node-type-filter', 'value'),
             Input('search-filter', 'value'),
             Input('relationship-direction', 'value'),
             Input('search-filter', 'search_value')],
            [State('graph', 'selectedNodeData')]
        )
        def update_graph(node_type, search_value, direction, search_input, selected_nodes):
            ctx = dash.callback_context
            if not ctx.triggered:
                return dash.no_update, dash.no_update

            # Update search options if search input changed
            if ctx.triggered[0]['prop_id'] == 'search-filter.search_value':
                if not search_input:
                    return dash.no_update, self._get_searchable_items()
                filtered_items = [
                    item for item in self._get_searchable_items()
                    if search_input.lower() in item['label'].lower()
                ]
                return dash.no_update, filtered_items

            try:
                selected_ids = [node['id'] for node in (selected_nodes or [])]
                
                # Convert node type 'all' to None for filter
                node_type = None if node_type == 'all' else node_type
                
                # Get all nodes and edges
                nodes, edges = self._create_nodes_and_edges()
                all_elements = nodes + edges
                
                # Apply filters if any are active
                if node_type or search_value or selected_ids:
                    # Get node IDs to keep
                    keep_nodes = set()
                    
                    # Filter by type
                    if node_type:
                        keep_nodes.update(n['data']['id'] for n in nodes if n['data'].get('type') == node_type)
                    else:
                        keep_nodes.update(n['data']['id'] for n in nodes)
                    
                    # Filter by search value
                    if search_value:
                        keep_nodes = {n for n in keep_nodes if search_value in n}
                    
                    # Filter by selected nodes and relationships
                    if selected_ids:
                        related_nodes = set(selected_ids)
                        
                        # Add related nodes based on direction
                        for edge in edges:
                            if edge['data']['type'] == 'calls':
                                source = edge['data']['source']
                                target = edge['data']['target']
                                
                                if source in selected_ids and direction in ['both', 'out']:
                                    related_nodes.add(target)
                                if target in selected_ids and direction in ['both', 'in']:
                                    related_nodes.add(source)
                        
                        keep_nodes = keep_nodes.intersection(related_nodes)
                    
                    # Keep only filtered nodes and their edges
                    filtered_nodes = [n for n in nodes if n['data']['id'] in keep_nodes]
                    filtered_edges = [e for e in edges if 
                                     (e['data']['source'] in keep_nodes and e['data']['target'] in keep_nodes)]
                    
                    # Highlight related edges
                    for edge in filtered_edges:
                        if edge['data']['type'] == 'calls':
                            edge['classes'] = 'relationship highlighted'
                    
                    all_elements = filtered_nodes + filtered_edges
                
                return all_elements, dash.no_update
            except Exception as e:
                print(f"Error in update_graph: {str(e)}")
                return dash.no_update, dash.no_update
            
        @app.callback(
            Output('node-details', 'children'),
            [Input('graph', 'tapNodeData')]
        )
        def display_node_data(node_data):
            if not node_data:
                return "Click a node to see details"
                
            try:
                if node_data['type'] == 'function':
                    metadata = node_data['metadata']
                    return html.Div([
                        html.H5(node_data['label']),
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