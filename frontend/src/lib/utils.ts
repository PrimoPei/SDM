import { dev } from '$app/environment';

export function randomSeed() {
	return BigInt(13248873089935215612 & (((1 << 63) - 1) * Math.random()));
}

export function base64ToBlob(base64image: string): Promise<Blob> {
	return new Promise((resolve) => {
		const img = new Image();
		img.onload = async () => {
			const w = img.width;
			const h = img.height;
			const canvas = document.createElement('canvas');
			canvas.width = w;
			canvas.height = h;
			const ctx = canvas.getContext('2d') as CanvasRenderingContext2D;
			ctx.drawImage(img, 0, 0, w, h);

			const imgBlob: Blob = await new Promise((_resolve) =>
				canvas.toBlob(_resolve, 'image/jpeg', 0.95)
			);
			resolve(imgBlob);
		};
		img.src = base64image;
	});
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
