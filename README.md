# Code Repository Graph Visualizer

An interactive visualization tool that extracts and displays function relationships in code repositories as an interactive graph.

## Features

- Repository Analysis:
  - Extracts folders, files, and functions
  - Captures function metadata (docstrings, parameters, types)
  - Maps relationships between functions
  
- Interactive Visualization:
  - Color-coded nodes for folders, files, and functions
  - Interactive filtering by node type and name
  - Function metadata display on hover
  - Input/output relationship filtering
  - Extension-based file coloring

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd code-graph-visualizer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the main script with a repository path:
```bash
python main.py --repo-path /path/to/repository
```

2. Access the interactive visualization at `http://localhost:8050`

### Command Line Arguments

- `--repo-path`: Path to the repository to analyze (required)
- `--cache`: Enable caching of analysis results (default: True)
- `--workers`: Number of parallel workers for analysis (default: 4)
- `--port`: Port for the visualization server (default: 8050)

## Project Structure

- `main.py`: Entry point and repository processing
- `scraper.py`: Function relationship extraction using AST
- `visualizer.py`: Interactive graph generation
- `filters.py`: Node filtering functionality
- `metadata.py`: Function metadata extraction
- `requirements.txt`: Project dependencies

## Visualization Controls

- **Node Filtering**: Use the dropdown menus to filter by node type or name
- **Relationship View**: Select nodes to view only their input/output relationships
- **Metadata View**: Hover over function nodes to see detailed information
- **Graph Navigation**: Zoom and pan using mouse controls

## Performance

- Parallel processing for large repositories
- Caching of analysis results
- Efficient graph rendering for large codebases 