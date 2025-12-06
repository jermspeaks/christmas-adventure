#!/usr/bin/env python3
"""
Generate all documentation files in the correct order.

This script generates:
1. DECISIONS.md (required first)
2. TODO_SECTIONS.md (depends on DECISIONS.md)
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Generating: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    
    if result.returncode != 0:
        print(f"\nError: Failed to generate {description}")
        sys.exit(result.returncode)
    
    print(f"✓ Successfully generated {description}")


def main():
    """Generate all documentation files."""
    scripts_dir = Path(__file__).parent
    project_root = scripts_dir.parent
    
    # Change to project root
    import os
    os.chdir(project_root)
    
    # Generate DECISIONS.md first
    decisions_script = scripts_dir / 'generate_decisions.py'
    if not decisions_script.exists():
        print(f"Error: {decisions_script} not found")
        sys.exit(1)
    
    run_command(
        [sys.executable, str(decisions_script)],
        "DECISIONS.md"
    )
    
    # Generate TODO_SECTIONS.md (depends on DECISIONS.md)
    todo_script = scripts_dir / 'generate_todo_sections.py'
    if not todo_script.exists():
        print(f"Error: {todo_script} not found")
        sys.exit(1)
    
    run_command(
        [sys.executable, str(todo_script)],
        "TODO_SECTIONS.md"
    )
    
    print("\n" + "="*60)
    print("✓ All documentation files generated successfully!")
    print("="*60)


if __name__ == '__main__':
    main()

