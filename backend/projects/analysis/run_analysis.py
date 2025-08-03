#!/usr/bin/env python3
"""
Simple script to run the segmentation analysis for the specific project.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from projects.analysis.analyze_project_segmentation import ProjectSegmentationAnalyzer


async def main():
    """Run analysis for the specific project."""
    project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"
    output_file = f"project_segmentation_analysis_{project_id}.csv"
    
    print(f"Starting analysis for project: {project_id}")
    print(f"Output will be saved to: {output_file}")
    
    analyzer = ProjectSegmentationAnalyzer()
    await analyzer.analyze_project(project_id, output_file)
    
    print(f"\nAnalysis complete! Check {output_file} for results.")


if __name__ == '__main__':
    asyncio.run(main()) 