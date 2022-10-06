<script lang="ts">
	import { zoom } from 'd3-zoom';
	import { select } from 'd3-selection';
	import { onMount } from 'svelte';
	import { PUBLIC_UPLOADS } from '$env/static/public';
	import { currZoomTransform, isPrompting, clickedPosition } from '$lib/store';
	import { round } from '$lib/utils';

	import { useMyPresence, useObject } from '$lib/liveblocks';
	import type { PromptImgObject } from '$lib/types';

	const myPresence = useMyPresence();
	const promptImgStorage = useObject('promptImgStorage');

	const height = 512 * 4;
	const width = 512 * 4;

	let canvasEl: HTMLCanvasElement;
	export { canvasEl as value };

	let containerEl: HTMLDivElement;
	let canvasCtx: CanvasRenderingContext2D;

	// keep track of images already rendered
	const imagesOnCanvas = new Set();

	function getpromptImgList(promptImgList: PromptImgObject[]): PromptImgObject[] {
		if (promptImgList) {
			const list: PromptImgObject[] = Object.values(promptImgList).sort((a, b) => a.date - b.date);
			return list.filter(({ id }) => !imagesOnCanvas.has(id));
		}
		return [];
	}
	let promptImgList: PromptImgObject[] = [];
	$: promptImgList = getpromptImgList($promptImgStorage?.toObject());

	$: if (promptImgList) {
		renderImages(promptImgList);
	}

	onMount(() => {
		const scale = width / containerEl.clientWidth;
		const zoomHandler = zoom()
			.scaleExtent([1 / scale / 2, 1])
			// .extent([
			// 	[0, 0],
			// 	[width, height]
			// ])
			.translateExtent([
				[-width * 0.3, -height * 0.3],
				[width * 1.3, height * 1.3]
			])
			.tapDistance(10)
			.on('zoom', zoomed);

		const selection = select(canvasEl.parentElement)
			.call(zoomHandler as any)
			.on('dblclick.zoom', () => {
				$isPrompting = true;
				$clickedPosition = $myPresence.cursor;
				console.log('clicked', $clickedPosition);
				return null;
			})
			.call(zoomHandler.scaleTo as any, 1 / scale / 1.5)
			.on('pointermove', handlePointerMove)
			.on('pointerleave', handlePointerLeave);

		canvasCtx = canvasEl.getContext('2d') as CanvasRenderingContext2D;
		function zoomReset() {
			console.log('zoom reset');
			const scale = width / containerEl.clientWidth;
			zoomHandler.scaleExtent([1 / scale / 2, 1]);
			selection.call(zoomHandler.scaleTo as any, 1 / scale / 1.5);
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
	function renderImages(promptImgList: PromptImgObject[]) {
		Promise.all(
			promptImgList.map(
				({ imgURL, position, id }) =>
					new Promise<ImageRendered>((resolve) => {
						const img = new Image();
						img.crossOrigin = 'anonymous';
						img.onload = () => {
							const res: ImageRendered = { img, position, id };
							canvasCtx.drawImage(img, position.x, position.y, img.width, img.height);
							resolve(res);
						};
						const url = imgURL.split('/');
						img.src = `${PUBLIC_UPLOADS}/${url.slice(3).join('/')}`;
					})
			)
		).then((images) => {
			images.forEach(({ img, position, id }) => {
				// keep track of images already rendered
				//re draw in order
				imagesOnCanvas.add(id);
				canvasCtx.drawImage(img, position.x, position.y, img.width, img.height);
			});
		});
	}
	function zoomed(e: Event) {
		const transform = ($currZoomTransform = e.transform);
		canvasEl.style.transform = `translate(${transform.x}px, ${transform.y}px) scale(${transform.k})`;
	}

	// Update cursor presence to current pointer location
	function handlePointerMove(event: PointerEvent) {
		event.preventDefault();
		const x = round($currZoomTransform.invertX(event.clientX));
		const y = round($currZoomTransform.invertY(event.clientY));

		myPresence.update({
			cursor: {
				x,
				y
			}
		});
	}

	// When the pointer leaves the page, set cursor presence to null
	function handlePointerLeave() {
		// myPresence.update({
		// 	cursor: null
		// });
	}
</script>

<div
	bind:this={containerEl}
	class="absolute top-0 left-0 right-0 bottom-0 overflow-hidden z-0 bg-gray-800"
>
	<canvas bind:this={canvasEl} {width} {height} class="absolute top-0 left-0 bg-white" />
	<slot />
</div>

<style lang="postcss" scoped>
	canvas {
		transform-origin: 0 0;
	}
</style>
