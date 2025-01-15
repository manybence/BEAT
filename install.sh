#!/bin/bash

# Check if requirements.txt exists
if [[ ! -f "requirements.txt" ]]; then
  echo "Error: requirements.txt not found."
  exit 1
fi

# Attempt to install using pip3
echo "Trying to install requirements using pip3..."
if pip3 install -r requirements.txt; then
  echo "All requirements installed successfully with pip3!"
  exit 0
fi

# Fallback to pip if pip3 fails
echo "pip3 failed. Trying pip..."
if pip install -r requirements.txt; then
  echo "All requirements installed successfully with pip!"
  exit 0
fi

# If both fail, show an error message
echo "Failed to install requirements with both pip3 and pip. Please check your environment."
exit 1
