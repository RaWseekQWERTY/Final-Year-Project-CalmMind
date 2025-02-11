/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html", // Include all HTML templates
    "./**/*.html",
    "./**/**/*.html",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}

