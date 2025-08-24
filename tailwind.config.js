/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './**/*.py'
  ],
  theme: {
    extend: {},
  },
  corePlugins: {
    preflight: false
  },
  plugins: [],
}
