const HtmlWebpackPlugin = require('html-webpack-plugin');
const webpack = require('webpack');

module.exports = env => {
  const config = {
    entry: './src/index.js',
    output: {
      path: __dirname + '/dist',
      publicPath: '/dist',
      filename: 'bundle.js'
    },
    module: {
      rules: [{
          test: /\.css$/,
          use: ['style-loader', 'css-loader']
        },

        // All files with a '.ts' or '.tsx' extension will be handled by 'ts-loader'.
        {
          test: /\.tsx?$/,
          loader: "ts-loader"
        },

        // All output '.js' files will have any sourcemaps re-processed by 'source-map-loader'.
        {
          test: /\.jsx?$/,
          use: ["babel-loader"],
          exclude: __dirname + '/node_modules'
        }
      ]
    },
    resolve: {
      extensions: ['*', '.js', '.jsx']
    },
    plugins: [
      new webpack.HotModuleReplacementPlugin(),
      new HtmlWebpackPlugin({
        title: "Crate App",
        filename: 'index.html',
        template: 'public/index.html',
      })
    ],
    devServer: {
      contentBase: './dist',
      hot: true
    },
    externals: {
      "React": "react",
      "ReactDOM": "react-dom"
    }
  }

  return config;
};
