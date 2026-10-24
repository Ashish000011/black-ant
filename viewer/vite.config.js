// Relative asset paths, so the built page works from GitHub Pages (/black-ant/) and from a plain folder.
// Three.js alone is about 500 kB minified, so the size warning starts above that.
export default { base: "./", build: { chunkSizeWarningLimit: 800 } };
