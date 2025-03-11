# Graph Code Viewer

A Python application that extracts and visualizes function and class relationships in code repositories.

## Features

- Extracts function and class metadata from code repositories
- Analyzes relationships between functions, methods, and classes
- Visualizes the code structure with an interactive graph
- Supports filtering by node type and relationship direction
- Provides detailed information about each code element

## Supported Languages

- Python
- JavaScript/TypeScript
- Java
- C/C++

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/graph-code-viewer.git
   cd graph-code-viewer
   ```

2. Create a conda environment and activate it:
   ```
   conda create -n gcvenv python=3.9
   conda activate gcvenv
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the application with:

```
python main.py --repo-path "path/to/your/repository"
```

Optional arguments:
- `--cache`: Enable/disable caching (default: True)
- `--workers`: Number of parallel workers for analysis (default: 4)
- `--port`: Port for the visualization server (default: 8050)

## How It Works

1. **Repository Scanning**: Analyzes all supported files in the repository
2. **Metadata Extraction**: Extracts function and class information
3. **Relationship Analysis**: Identifies how functions and classes interact
4. **Visualization**: Creates an interactive graph of the codebase structure

## Project Structure

- `main.py`: Entry point for the application
- `metadata.py`: Handles code metadata extraction
- `scraper.py`: Manages repository scanning and relationship analysis
- `filters.py`: Provides filtering capabilities for the visualization
- `visualizer.py`: Creates the interactive graph visualization 