import { dev } from '$app/environment';

export function randomSeed() {
	return BigInt(13248873089935215612 & (((1 << 63) - 1) * Math.random()));
}
export async function uploadImage(imagBlob: Blob, prompt: string): string {
	// simple regex slugify string	for file name
	const promptSlug = slugify(prompt);
	const UPLOAD_URL = dev ? 'moon/uploads' : 'https://huggingface.co/uploads';

	const hash = crypto.randomUUID().split('-')[0];
	const fileName = `color-palette-${hash}-${promptSlug}.jpeg`;

	const file = new File([imagBlob], fileName, { type: 'image/jpeg' });

	console.log('uploading image', file);

	const response = await fetch(UPLOAD_URL, {
		method: 'POST',
		headers: {
			'Content-Type': file.type,
			'X-Requested-With': 'XMLHttpRequest'
		},
		body: file /// <- File inherits from Blob
	});
	const url = await response.text();

	console.log('uploaded images', url);
	return url;
}

function slugify(text: string) {
	if (!text) return '';
	return text
		.toString()
		.toLowerCase()
		.replace(/\s+/g, '-')
		.replace(/[^\w\-]+/g, '')
		.replace(/\-\-+/g, '-')
		.replace(/^-+/, '')
		.replace(/-+$/, '');
}
