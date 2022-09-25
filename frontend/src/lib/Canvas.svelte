<script lang="ts">
	import { zoom, type ZoomTransform, zoomIdentity } from 'd3-zoom';
	import { select } from 'd3-selection';
	import { onMount } from 'svelte';
	import { currZoomTransform } from '$lib/store';
	const height = 512 * 5;
	const width = 512 * 5;

	let canvasEl: HTMLCanvasElement;
	let containerEl: HTMLDivElement;
	let canvasCtx: CanvasRenderingContext2D;

	$:{
		console.log($currZoomTransform)
	}
	const margin = { top: 100, right: 100, bottom: 100, left: 100 };
	const extent = [
		[-margin.left, -margin.top],
		[width + margin.right, height + margin.bottom]
	] as [[number, number], [number, number]];
	onMount(() => {
		const scale = width / containerEl.clientWidth;
		const zoomHandler = zoom()
			.scaleExtent([1 / scale / 2, 2])
			.translateExtent([
				[0, 0],
				[width, height]
			])
			// .translateExtent(extent)
			.clickDistance(2)
			.on('zoom', zoomed);

		select(canvasEl.parentElement)
			.call(zoomHandler as any)
			.call(zoomHandler.scaleTo as any, 1 / scale)
			.on('pointermove', handlePointerMove)
			.on('pointerleave', handlePointerLeave);

		canvasCtx = canvasEl.getContext('2d') as CanvasRenderingContext2D;
		canvasCtx.fillStyle = 'red';
		canvasCtx.rect(10, 10, 160, 90);
		canvasCtx.fill();
		canvasCtx.strokeStyle = 'blue';
		canvasCtx.lineWidth = 5;
		canvasCtx.strokeRect(0, 0, width, height);
	});

	function zoomed(e: Event) {
		const transform = ($currZoomTransform = e.transform);
		console.log(canvasEl.style.transform, transform);
		canvasEl.style.transform = `translate(${transform.x}px, ${transform.y}px) scale(${transform.k})`;
	}
	function handlePointerMove(e: PointerEvent) {
		// console.log(e);
	}
	function handlePointerLeave(e: PointerEvent) {
		// console.log(e);
	}
</script>

<div
	bind:this={containerEl}
	class="fixed w-screen h-screen top-0 left-0 overflow-hidden border-4 border-black"
>
	<canvas bind:this={canvasEl} {width} {height} class="absolute top-0 left-0" />
</div>

<style lang="postcss" scoped>
	canvas {
		transform-origin: 0 0;
	}
</style>
