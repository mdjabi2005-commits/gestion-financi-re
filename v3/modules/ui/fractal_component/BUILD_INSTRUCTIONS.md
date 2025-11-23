# 🔧 Building the Sierpinski Fractal Navigation Component

This document explains how to build the custom Streamlit component for the interactive triangle-based navigation.

## Prerequisites

You need to have Node.js and npm installed on your system.

### Download Node.js

1. Go to https://nodejs.org/
2. Download the **LTS (Long Term Support)** version
3. Run the installer and follow the instructions
4. Verify installation by opening a terminal and running:
   ```bash
   node --version
   npm --version
   ```

## Building the Component

### Step 1: Navigate to the Component Directory

```bash
cd "C:\Users\djabi\gestion-financière\v3\modules\ui\fractal_component"
```

### Step 2: Install Dependencies

```bash
npm install
```

This will:
- Create a `node_modules/` folder
- Download webpack, babel, and streamlit dependencies
- Set up the build environment

**Note:** This may take a few minutes on first run.

### Step 3: Build the Component

```bash
npm run build
```

This will:
- Compile JavaScript code with Babel
- Bundle with Webpack
- Create `build/index.js` (the compiled component)
- Output size and status

### Step 4: Verify the Build

Check that the `build/` directory now contains:
```
build/
├── index.js          (compiled component)
└── index.js.map      (sourcemap for debugging)
```

If you see these files, the build was successful! ✅

## Development Mode

If you want to make changes and auto-rebuild:

```bash
npm run dev
```

This watches for file changes and rebuilds automatically.

## Troubleshooting

### Issue: "npm: command not found"
**Solution:** Node.js is not installed. Download and install from https://nodejs.org/

### Issue: "Webpack not found"
**Solution:** Run `npm install` again in the component directory

### Issue: Build fails with syntax errors
**Solution:** Check the frontend/fractal.js file for JavaScript errors

### Issue: "Permission denied" on macOS/Linux
**Solution:** Run `sudo npm install` instead

## Using the Compiled Component

Once built, the component is automatically used by:
- `modules/ui/fractal_component/backend.py`
- Which is imported in `pages/fractal_view.py`

Simply run your Streamlit app:
```bash
cd "C:\Users\djabi\gestion-financière\v3"
streamlit run pages/fractal_view.py
```

The Sierpinski triangles should now appear! 🔺

## File Structure

```
modules/ui/fractal_component/
├── backend.py                  # Python integration
├── __init__.py                 # Package exports
├── package.json               # npm dependencies
├── webpack.config.js          # Build configuration
├── streamlit.json             # Component metadata
├── .babelrc                   # JavaScript transpilation
├── frontend/
│   ├── index.js              # Streamlit integration
│   ├── fractal.js            # Core algorithm (SOURCE)
│   ├── fractal.css           # Styling
│   └── index.html            # HTML template
└── build/                     # Generated (DO NOT EDIT)
    ├── index.js              # Compiled component
    └── index.js.map          # Source map
```

## What Gets Compiled?

- **Source:** `frontend/fractal.js` + `frontend/index.js`
- **Output:** `build/index.js` (single bundled file)
- **Format:** UMD (Universal Module Definition)
- **Dependencies:** streamlit-component-lib bundled in

## Notes

- The `build/` folder is ignored by git (in .gitignore)
- You must rebuild after modifying `frontend/fractal.js`
- Node modules are large (~400MB) - also in .gitignore
- The build takes 5-10 seconds on a modern machine

Enjoy your interactive fractals! 🎨
