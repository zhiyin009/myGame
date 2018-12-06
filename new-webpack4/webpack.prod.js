const merge = require('webpack-merge');
const common = require('./webpack.common');

module.exports = env => {
  const config = merge(common(), {
    mode: 'production',
  });
  return config;
};
