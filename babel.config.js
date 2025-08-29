module.exports = function (api) {
  api.cache(true);
  return {
    presets: ["babel-preset-expo"],
    plugins: [
      [
        "module-resolver",
        {
          root: ["."],
          extensions: [".ts", ".tsx", ".js", ".jsx", ".json"],
          alias: {
            "@/components": "./src/components",
            "@/screens": "./src/screens",
            "@/api": "./src/api",
            "@/storage": "./src/storage",
            "@/config": "./src/config.ts"
          }
        }
      ]
    ]
  };
};
