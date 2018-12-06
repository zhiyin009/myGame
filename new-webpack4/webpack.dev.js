const merge = require('webpack-merge');
const common = require('./webpack.common.js');

module.exports = env => {
  const config = merge(common(), {
    mode: 'development',
    devServer: {
      host: "127.0.0.1",
      port: "8800",
      disableHostCheck: true,
    }
  });

  return config;
};
