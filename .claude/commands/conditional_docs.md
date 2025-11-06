# Conditional Documentation Guide

This prompt helps you determine what documentation you should read based on the specific changes you need to make in the codebase. Review the conditions below and read the relevant documentation before proceeding with your task.

## Instructions
- Review the task you've been asked to perform
- Check each documentation path in the Conditional Documentation section
- For each path, evaluate if any of the listed conditions apply to your task
  - IMPORTANT: Only read the documentation if any one of the conditions match your task
- IMPORTANT: You don't want to excessively read documentation. Only read the documentation if it's relevant to your task.

## Conditional Documentation

- README.md
  - Conditions:
    - When operating on anything under src
    - When first understanding the project structure

- app_docs/feature-minecraft-transformation-extraction.md
  - Conditions:
    - When working with Minecraft wiki data extraction or parsing
    - When modifying transformation parsers (crafting, smelting, trading, etc.)
    - When adding new transformation types or data models
    - When troubleshooting CSV output or data validation issues
    - When implementing graph construction from transformation data
    - When debugging BeautifulSoup HTML parsing for wiki pages

- app_docs/feature-crafting-category-metadata.md
  - Conditions:
    - When working with crafting recipe categories or section metadata
    - When implementing filtering or organization by recipe category
    - When troubleshooting category extraction or normalization
    - When adding category metadata to other transformation types
    - When modifying the parse_crafting() function or category extraction logic

- app_docs/feature-0-graphviz-visualization.md
  - Conditions:
    - When working with graph visualization or Graphviz integration
    - When implementing or modifying visual representations of transformations
    - When adding new output formats or rendering options
    - When troubleshooting graph generation or layout issues
    - When customizing colors, styles, or graph appearance
    - When implementing filtering for graph visualization
    - When handling multi-input transformations in visualizations

- app_docs/feature-1-3d-graph-visualization.md
  - Conditions:
    - When working with 3D graph visualization or NetworkX integration
    - When implementing interactive visualizations using Matplotlib
    - When working with spectral or spring layout algorithms
    - When troubleshooting 3D rendering or layout computation issues
    - When implementing node sizing based on degree centrality
    - When handling multi-input transformations with intermediate nodes in 3D space
    - When comparing 2D vs 3D visualization approaches
    - When modifying src/visualize_graph_3d.py or tests/test_visualize_graph_3d.py

- app_docs/feature-2-3d-graph-hover-interactivity.md
  - Conditions:
    - When implementing hover annotations or tooltips in matplotlib
    - When working with matplotlib event handlers (motion_notify_event)
    - When implementing interactive features in 3D scatter plots
    - When troubleshooting hover detection or annotation positioning
    - When adding numeric axis scales or tick configuration
    - When working with matplotlib toolbar visibility
    - When implementing hit testing with scatter plot contains() method
    - When enhancing user interaction in 3D visualizations

