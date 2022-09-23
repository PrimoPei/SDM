<script lang="ts">
	import { zoom, zoomIdentity } from 'd3-zoom';
	import { select, type Selection } from 'd3-selection';
	import { onMount, tick } from 'svelte';

	const width = 512 * 2;
	const height = 512 * 2;

	let canvasEl: HTMLCanvasElement;
	let canvasCtx: CanvasRenderingContext2D;

	const margin = { top: 50, right: 50, bottom: 50, left: 50 };
	const extent = [
		[margin.left, margin.top],
		[width - margin.right, height - margin.top]
	] as [[number, number], [number, number]];

	const zoomHandler = zoom()
		.scaleExtent([0.5, 2])
		// .translateExtent(extent)
		.extent(extent)
		.on('zoom', zoomed);

	onMount(() => {
		select(canvasEl.parentElement)
			.call(zoomHandler as any)
			.call(zoomHandler.transform as any, zoomIdentity);
		canvasCtx = canvasEl.getContext('2d') as CanvasRenderingContext2D;
		canvasCtx.fillStyle = 'red';
		canvasCtx.rect(100, 100, 500, 500);
		canvasCtx.fill();
	});

	function zoomed(e: Event) {
		const transform = e.transform;
		console.log(canvasEl.style.transform, transform);
		tick().then(() => {
			canvasEl.style.transform = `translate(${transform.x}px, ${transform.y}px) scale(${transform.k})`;
		});
	}
</script>

<div class="fixed w-screen h-screen top-0 left-0 overflow-hidden border-4 border-black">
	<canvas bind:this={canvasEl} {width} {height} />
</div>

<style lang="postcss" scoped>
	canvas {
		transform-origin: 0 0;
	}
</style>
