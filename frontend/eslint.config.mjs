import nextVitals from "eslint-config-next/core-web-vitals";

export default [
  ...nextVitals,
  {
    ignores: ["dist/**", ".next/**", "node_modules/**"],
    rules: {
      "react-hooks/set-state-in-effect": "off",
      "react-hooks/immutability": "off",
      "react-hooks/purity": "off"
    }
  },
];
