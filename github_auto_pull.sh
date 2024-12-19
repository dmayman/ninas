#!/bin/bash

# Wait for the network to initialize
sleep 10

# Navigate to your repository
cd /ninas

# Pull the latest changes
git pull origin main

# Optional: Run a specific script after pulling (if needed)
# ./your_script.sh