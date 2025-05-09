#!/bin/bash

# Setup script for general_analysis
# Combines elements from interactive_analysis and evaluator_analysis

echo "Setting up general_analysis environment..."

# Install NPM dependencies
npm install

# Create necessary directories if they don't exist
mkdir -p public/data
mkdir -p figures
mkdir -p src

# Copy public data files from both analysis directories
echo "Copying data files from interactive_analysis and evaluator_analysis..."

# From interactive_analysis
cp ../interactive_analysis/public/enhanced_master_data.csv public/data/
cp ../interactive_analysis/public/master_results.csv public/data/
cp ../interactive_analysis/public/model_comparison.csv public/data/
cp ../interactive_analysis/public/*.csv public/data/

# From evaluator_analysis
cp ../evaluator_analysis/public/*.csv public/data/

# Copy visualization figures
echo "Copying visualization figures..."
cp ../interactive_analysis/figures/* figures/

# Create Vite config
echo "Setting up Vite config..."
cat > vite.config.js << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
EOF

# Create PostCSS config
echo "Setting up PostCSS config..."
cat > postcss.config.js << 'EOF'
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
EOF

# Create Tailwind config
echo "Setting up Tailwind config..."
cat > tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
EOF

# Create index.html
echo "Creating index.html..."
cat > index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Jailbreak Analysis</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
EOF

# Create CSS file
echo "Creating index.css..."
cat > src/index.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.chart-container {
  margin: 1rem 0;
  padding: 1rem;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  background-color: white;
}
EOF

# Create main.jsx file
echo "Creating main.jsx..."
cat > src/main.jsx << 'EOF'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
EOF

# Create App.jsx file
echo "Creating App.jsx..."
cat > src/App.jsx << 'EOF'
import React from 'react'
import CombinedVisualization from './CombinedVisualization'

function App() {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Jailbreak Analysis Visualization</h1>
      <CombinedVisualization />
    </div>
  )
}

export default App
EOF

echo "Setup complete! Run 'npm run dev' to start the development server." 