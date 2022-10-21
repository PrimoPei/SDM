import colors from 'tailwindcss/colors';

export const COLORS = Object.values(colors)
	.filter((e) => typeof e === 'object')
	.map((e) => e['200'])
	.slice(0, 18);

export const EMOJIS = ['🐝', '🐌', '🐞', '🐜', '🦋', '🐛', '🐝', '🐞', '🦟', '🦗', '🕷', '🦂', '🐢', '🐍', '🦎', '🦖', '🦕', '🐙', '🦑', '🐠', '🐟', '🐡', '🐬', '🦈', '🐳', '🐋', '🐊', '🐅', '🐆', '🦓', '🦍', '🦧', '🐘', '🦛', '🦏', '🐪', '🐫', '🦒', '🐃', '🐂', '🐄', '🐎', '🐖',
	'🐏', '🐑', '🐐', '🐕', '🐩', '🐈', '🐓', '🦃', '🦅', '🦆', '🦢', '🦉', '🦚', '🦜', '🦇', '🐁', '🐀', '🐿', '🐇', '🐿', '🦔', '🦇', '🐻', '🐻', '🐨', '🐼', '🐵', '🙈', '🙉', '🙊', '🐒', '🐉', '🐲', '🦕', '🦖', '🐊', '🐢', '🦎', '🐍', '🐦', '🐧', '🦅', '🦆', '🦉', '🦇']

export const MAX_CAPACITY = 20;

export const CANVAS_SIZE = {
	width: 512 * 6,
	height: 512 * 6,
}
export const GRID_SIZE = 32

export const FRAME_SIZE = 512