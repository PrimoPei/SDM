/** @type {import('tailwindcss').Config} */
module.exports = {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {},
	plugins: [require('@tailwindcss/forms'), require('@tailwindcss/line-clamp')]
};
