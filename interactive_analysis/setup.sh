#!/bin/bash

# Install or update nvm
echo "Installing/updating nvm..."
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Load nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Install Node.js v18 (LTS)
echo "Installing Node.js v18..."
nvm install 18
nvm use 18

# Print Node.js and npm versions
echo "Node.js version: $(node -v)"
echo "npm version: $(npm -v)"

# Install dependencies
echo "Installing dependencies..."
npm install

# Create public directory if it doesn't exist
mkdir -p public

echo "Setup complete! You can now run 'npm start' to start the development server."
echo ""
echo "Note: If you're setting this up for the first time, you may need to:"
echo "1. Close and reopen your terminal"
echo "2. Run 'nvm use 18' again"
echo "3. Then run 'npm start'" 