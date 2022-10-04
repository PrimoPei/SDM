<script lang="ts">
	import { zoom, type ZoomTransform, zoomIdentity } from 'd3-zoom';
	import { select } from 'd3-selection';
	import { onMount } from 'svelte';
	import { PUBLIC_UPLOADS } from '$env/static/public';
	import {
		currZoomTransform,
		myPresence,
		isPrompting,
		clickedPosition,
		imagesList
	} from '$lib/store';

	const height = 512 * 5;
	const width = 512 * 5;

	let canvasEl: HTMLCanvasElement;
	export { canvasEl as value };
	let value = canvasEl;

	let containerEl: HTMLDivElement;
	let canvasCtx: CanvasRenderingContext2D;

	$: if ($imagesList) {
		renderImages($imagesList);
	}

	onMount(() => {
		const scale = width / containerEl.clientWidth;
		const zoomHandler = zoom()
			.scaleExtent([1 / scale / 1.5, 1])
			// .extent([
			// 	[0, 0],
			// 	[width, height]
			// ])
			.translateExtent([
				[-width * 0.1, -height * 0.1],
				[width * 1.1, height * 1.1]
			])
			.tapDistance(10)
			.on('zoom', zoomed);

		select(canvasEl.parentElement)
			.call(zoomHandler as any)
			.on('dblclick.zoom', () => {
				$isPrompting = true;
				$clickedPosition = $myPresence.cursor;
				console.log('clicked', $clickedPosition);
				return null;
			})
			// .call(zoomHandler.scaleTo as any, 1 / scale)
			.on('pointermove', handlePointerMove)
			.on('pointerleave', handlePointerLeave);

		canvasCtx = canvasEl.getContext('2d') as CanvasRenderingContext2D;
		canvasCtx.strokeStyle = 'blue';
		canvasCtx.lineWidth = 10;
		canvasCtx.strokeRect(0, 0, width, height);
	});

	function renderImages(imagesList) {
		const images = [...imagesList.toImmutable()].sort((a, b) => a.date - b.date);
		Promise.all(
			images.map(
				({ imgURL, position }) =>
					new Promise((resolve) => {
						const img = new Image();
						img.crossOrigin = 'anonymous';
						img.onload = () => {
							resolve({ img, position });
						};
						const url = imgURL.split('/');
						img.src = `${PUBLIC_UPLOADS}/${url.slice(3).join('/')}`;
					})
			)
		).then((images) => {
			images.forEach(({ img, position }) => {
				canvasCtx.drawImage(img, position.x, position.y, img.width, img.height);
			});
		});
	}
	function zoomed(e: Event) {
		const transform = ($currZoomTransform = e.transform);
		canvasEl.style.transform = `translate(${transform.x}px, ${transform.y}px) scale(${transform.k})`;
	}

	const r = 8;
	function round(p, n) {
		return p % n < n / 2 ? p - (p % n) : p + n - (p % n);
	}
	const grid = 10;

	// Update cursor presence to current pointer location
	function handlePointerMove(event: PointerEvent) {
		event.preventDefault();
		const x = Math.round($currZoomTransform.invertX(event.layerX) / grid) * grid;
		const y = Math.round($currZoomTransform.invertY(event.layerY) / grid) * grid;
		// const x = Math.round(event.layerX / grid) * grid; //round(Math.max(r, Math.min(512 * 5 - r, event.clientX)), 100);
		// const y = Math.round(event.layerY / grid) * grid; //round(Math.max(r, Math.min(512 * 5 - r, event.clientY)), 100);
		// const x = round(Math.max(r, Math.min(512 * 5 - r, event.clientX)), grid);
		// const y = round(Math.max(r, Math.min(512 * 5 - r, event.clientY)), grid);
		$myPresence = {
			cursor: {
				x,
				y
			}
		};
	}

	// When the pointer leaves the page, set cursor presence to null
	function handlePointerLeave() {
		$myPresence = {
			cursor: null
		};
	}
</script>

<div bind:this={containerEl} class="absolute top-0 left-0 right-0 bottom-0 overflow-hidden z-0">
	<canvas bind:this={canvasEl} {width} {height} class="absolute top-0 left-0" />
</div>

<style lang="postcss" scoped>
	canvas {
		transform-origin: 0 0;
	}
</style>
