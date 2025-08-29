import "dotenv/config";

export default {
  expo: {
    name: "bleep",
    slug: "bleep",
    version: "1.0.0",
    extra: {
      BACKEND_URL: process.env.BACKEND_URL
    }
  }
};
