import { globalIgnores } from "eslint/config";
import {
  defineConfigWithVueTs,
  vueTsConfigs,
} from "@vue/eslint-config-typescript";
import pluginVue from "eslint-plugin-vue";
import pluginVitest from "@vitest/eslint-plugin";

export default defineConfigWithVueTs(
  {
    name: "app/files-to-lint",
    files: ["**/*.{vue,ts,mts,tsx}"],
  },

  globalIgnores(["**/dist/**", "**/dist-ssr/**", "**/coverage/**", "tests/**"]),

  ...pluginVue.configs["flat/essential"],
  vueTsConfigs.recommended,

  {
    ...pluginVitest.configs.recommended,
    files: ["src/**/__tests__/*"],
  },

  {
    rules: {
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-unused-vars": "warn",
      "@typescript-eslint/no-unused-expressions": "warn",
      "prefer-const": "warn",
      "vue/multi-word-component-names": "warn",
      "vue/no-dupe-keys": "warn",
      "vue/no-mutating-props": "warn",
      "vue/no-parsing-error": "warn",
      "vue/valid-attribute-name": "warn",
      "vue/valid-template-root": "warn",
    },
  },

  {
    files: ["**/*.vue"],
    rules: {
      "@typescript-eslint/no-unused-vars": "off",
      "vue/no-unused-vars": ["warn", { ignorePattern: "^_" }],
    },
  },
);
