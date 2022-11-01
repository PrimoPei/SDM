<script lang="ts">
	import { zoom, zoomIdentity } from 'd3-zoom';
	import { min } from 'd3-array';
	import { select } from 'd3-selection';
	import { onMount } from 'svelte';
	import { PUBLIC_UPLOADS } from '$env/static/public';
	import { currZoomTransform, canvasEl, isRenderingCanvas, canvasSize } from '$lib/store';

	import { useMyPresence, useObject } from '$lib/liveblocks';
	import { LiveObject } from '@liveblocks/client';

	import type { PromptImgObject } from '$lib/types';
	import { FRAME_SIZE, GRID_SIZE } from '$lib/constants';

	const myPresence = useMyPresence({ addToHistory: true });
	const promptImgStorage = useObject('promptImgStorage');

	const height = $canvasSize.height;
	const width = $canvasSize.width;

	let containerEl: HTMLDivElement;
	let canvasCtx: CanvasRenderingContext2D;

	const imagesOnCanvas = new Set();

	function getpromptImgList(
		promptImgList: Record<string, LiveObject<PromptImgObject> | PromptImgObject>
	): PromptImgObject[] {
		if (promptImgList) {
			//sorted by last updated
			const canvasPixels = new Map();
			for (const x of Array.from(Array(width / GRID_SIZE).keys())) {
				for (const y of Array.from(Array(height / GRID_SIZE).keys())) {
					canvasPixels.set(`${x * GRID_SIZE}_${y * GRID_SIZE}`, null);
				}
			}
			const list: PromptImgObject[] = Object.values(promptImgList)
				.map((e) => {
					if (e instanceof LiveObject) {
						return e.toObject();
					} else {
						return e;
					}
				})
				.sort((a, b) => b.date - a.date);
			// init
			for (const promptImg of list) {
				const x = promptImg.position.x;
				const y = promptImg.position.y;
				for (const i of [...Array(FRAME_SIZE / GRID_SIZE).keys()]) {
					for (const j of [...Array(FRAME_SIZE / GRID_SIZE).keys()]) {
						const key = `${x + i * GRID_SIZE}_${y + j * GRID_SIZE}`;
						if (!canvasPixels.get(key)) {
							canvasPixels.set(key, promptImg.id);
						}
					}
				}
			}
			const ids = new Set([...canvasPixels.values()]);
			const filteredImages = list.filter((promptImg) => ids.has(promptImg.id));
			return filteredImages.reverse().filter((promptImg) => !imagesOnCanvas.has(promptImg.id));
		}
		return [];
	}
	let promptImgList: PromptImgObject[] = [];
	$: promptImgList = getpromptImgList($promptImgStorage?.toObject());

	$: if (promptImgList) {
		renderImages(promptImgList);
	}

	function to_bbox(
		W: number,
		H: number,
		center: { x: number; y: number },
		w: number,
		h: number,
		margin: number
	) {
		//https://bl.ocks.org/fabiovalse/b9224bfd64ca96c47f8cdcb57b35b8e2
		const kw = (W - margin) / w;
		const kh = (H - margin) / h;
		const k = min([kw, kh]) || 1;
		const x = W / 2 - center.x * k;
		const y = H / 2 - center.y * k;
		return zoomIdentity.translate(x, y).scale(k);
	}
	onMount(() => {
		const padding = 50;
		const scale =
			(width + padding * 2) /
			(containerEl.clientHeight > containerEl.clientWidth
				? containerEl.clientWidth
				: containerEl.clientHeight);
		const zoomHandler = zoom()
			.scaleExtent([1 / scale / 2, 3])
			// .translateExtent([
			// 	[-padding, -padding],
			// 	[width + padding, height + padding]
			// ])
			.tapDistance(10)
			.on('zoom', zoomed);

		const selection = select($canvasEl.parentElement)
			.call(zoomHandler as any)
			.call(
				zoomHandler.transform as any,
				to_bbox(
					containerEl.clientWidth,
					containerEl.clientHeight,
					{ x: width / 2, y: height / 2 },
					width,
					height,
					padding
				)
			)
			// .call(zoomHandler.scaleTo as any, 1 / scale)
			.on('pointermove', handlePointerMove)
			.on('pointerleave', handlePointerLeave);

		canvasCtx = $canvasEl.getContext('2d') as CanvasRenderingContext2D;
		function zoomReset() {
			const scale =
				(width + padding * 2) /
				(containerEl.clientHeight > containerEl.clientWidth
					? containerEl.clientWidth
					: containerEl.clientHeight);
			zoomHandler.scaleExtent([1 / scale / 2, 3]);
			selection.call(
				zoomHandler.transform as any,
				to_bbox(
					containerEl.clientWidth,
					containerEl.clientHeight,
					{ x: width / 2, y: height / 2 },
					width,
					height,
					padding
				)
			);
		}
		window.addEventListener('resize', zoomReset);
		return () => {
			window.removeEventListener('resize', zoomReset);
		};
	});

	type ImageRendered = {
		img: HTMLImageElement;
		position: { x: number; y: number };
		id: string;
	};
	async function renderImages(promptImgList: PromptImgObject[]) {
		if (promptImgList.length === 0) return;
		$isRenderingCanvas = true;

		await Promise.allSettled(
			promptImgList.map(
				({ imgURL, position, id, room }) =>
					new Promise<ImageRendered>((resolve, reject) => {
						const img = new Image();
						img.crossOrigin = 'anonymous';
						img.onload = () => {
							const res: ImageRendered = { img, position, id };
							canvasCtx.drawImage(img, position.x, position.y, img.width, img.height);
							resolve(res);
						};
						img.onerror = (err) => {
							reject(err);
						};
						img.src = `${PUBLIC_UPLOADS}/${room}/${imgURL}`;
					})
			)
		).then((values) => {
			const images = values
				.filter((v) => v.status === 'fulfilled')
				.map((v) => (v as PromiseFulfilledResult<ImageRendered>).value);
			images.forEach(({ img, position, id }) => {
				// keep track of images already rendered
				//re draw in order
				imagesOnCanvas.add(id);
				canvasCtx.drawImage(img, position.x, position.y, img.width, img.height);
			});
		});
		$isRenderingCanvas = false;
	}
	function zoomed(e: Event) {
		const transform = ($currZoomTransform = e.transform);
		$canvasEl.style.transform = `translate(${transform.x}px, ${transform.y}px) scale(${transform.k})`;
	}

	// Update cursor presence to current pointer location
	function handlePointerMove(event: PointerEvent) {
		event.preventDefault();
		const x = $currZoomTransform.invertX(event.clientX);
		const y = $currZoomTransform.invertY(event.clientY);

		myPresence.update({
			cursor: {
				x,
				y
			}
		});
	}

	// When the pointer leaves the page, set cursor presence to null
	function handlePointerLeave() {
		myPresence.update({
			cursor: null
		});
	}
</script>

<div
	bind:this={containerEl}
	class="absolute top-0 left-0 right-0 bottom-0 overflow-hidden z-0 bg-blue-200"
>
	<canvas
		bind:this={$canvasEl}
		{width}
		{height}
		class="absolute top-0 left-0 bg-white shadow-2xl shadow-blue-500/20"
	/>
	<slot />
</div>

<style lang="postcss" scoped>
	canvas {
		transform-origin: 0 0;
	}
</style>
