import { PUBLIC_UPLOAD_URL } from '$env/static/public';

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

			const imgBlob: Blob = await new Promise((r) =>
				canvas.toBlob(r as BlobCallback, 'image/jpeg', 0.95)
			);
			resolve(imgBlob);
		};
		img.src = base64image;
	});
}
export async function uploadImage(imagBlob: Blob, prompt: string, key: string): Promise<string> {
	// simple regex slugify string	for file name
	const promptSlug = slugify(prompt);

	const hash = crypto.randomUUID().split('-')[0];
	const fileName = `color-palette-${hash}-${promptSlug}-${key}.jpeg`;

	const file = new File([imagBlob], fileName, { type: 'image/jpeg' });

	const formData = new FormData()
	formData.append('file', file)

	console.log('uploading image', file);

	const response = await fetch(PUBLIC_UPLOAD_URL, {
		method: 'POST',
		body: formData
	});
	const res = await response.json();

	console.log('uploaded images', res);
	return res.filename;
}
const MAX = 512 * 5 - 512

export function round(pos: number, size = 32) {
	const value = pos % size < size / 2 ? pos - (pos % size) : pos + size - (pos % size);
	return Math.max(0, Math.min(Math.round(value), MAX))
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