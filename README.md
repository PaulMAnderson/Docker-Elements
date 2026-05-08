# Neuroscience & Data Science Docker Standards

A collection of modular, production-ready Docker containers designed for neuroscience research and data science. These images are optimized for deployment on remote servers (Unraid, cloud instances, etc.) and follow a hierarchical structure where specialized tools build upon robust base images.

## Vision
The goal of this repository is to provide a "family" of containers that can be used independently or combined to create comprehensive analysis environments. By standardizing the base layers and toolsets, we ensure reproducibility across different research hardware and locations.

## Image Hierarchy
- **Base Layers**: Foundational Ubuntu-based images with core dependencies (Python, Node.js, common utilities).
- **Core Tools**: Images providing primary interfaces like JupyterLab, SSH access, and File management.
- **Specialized Toolsets**:
  - `matlab+ephys`: MATLAB environment combined with electrophysiology tools (SpikeInterface, Neo, OpenEphys).
  - `dlc`: DeepLabCut for pose estimation.
  - `cebra`, `lfads`, `lightning-pose`: Specialized modeling and analysis frameworks.
  - `phy`: Spike sorting visualization.

## Usage
These containers are designed to be configured via environment variables (see `.env.example`) and deployed using `docker run` or Docker Compose.

### Remote Deployment (Unraid/Cloud)
1. Map your data shares to `/mnt/data`.
2. Configure your specific credentials (DataJoint, GCloud, etc.) via the container environment settings.
3. Access tools via web interfaces (Jupyter on port 8888) or SSH.

## Building
Images are designed to be built sequentially if modifying base layers. Each subdirectory contains its own `dockerfile` and supporting scripts.
