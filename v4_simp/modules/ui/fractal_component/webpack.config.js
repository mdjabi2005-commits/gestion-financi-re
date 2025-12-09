const path = require('path');

module.exports = {
  mode: 'production',
  entry: './frontend/index.js',
  output: {
    path: path.resolve(__dirname, 'build'),
    filename: 'index.js',
    library: 'FractalNavigation',
    libraryTarget: 'umd'
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env']
          }
        }
      }
    ]
  },
  externals: {
    'streamlit-component-lib': 'streamlit-component-lib'
  },
  resolve: {
    extensions: ['.js', '.json']
  }
};
