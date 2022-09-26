import colors from 'tailwindcss/colors';

export const COLORS = Object.values(colors)
	.filter((e) => typeof e === 'object')
	.map((e) => e['200'])
	.slice(0, 18);

// all animal emojis list
export const EMOJIS = [
	'🐶',
	'🐱',
	'🐭',
	'🐹',
	'🐰',
	'🦊',
	'🐻',
	'🐼',
	'🐨',
	'🐯',
	'🦁',
	'🐮',
	'🐲',
	'🌚',
	'🌝',
	'🌞',
	'🌛',
	'🌜'
];
