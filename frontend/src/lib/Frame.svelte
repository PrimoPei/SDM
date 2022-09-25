<script lang="ts">
	import { spring } from 'svelte/motion';
	import type { ZoomTransform } from 'd3-zoom';

	export let transform: ZoomTransform;
	export let color = '';
	export let x = 0;
	export let y = 0;

	// Spring animation for cursor
	const coords = spring(
		{ x, y },
		{
			stiffness: 0.07,
			damping: 0.35
		}
	);
	// Update spring when x and y change
	$: coords.set({ x, y });
</script>

<div
	class="frame"
	style={`transform: translateX(${$coords.x}px) translateY(${$coords.y}px) scale(${transform.k})`}
/>

<style lang="postcss" scoped>
	.frame {
		@apply absolute top-0 left-0 border-2 border-sky-500 bg-gradient-to-b from-sky-200 w-[512px] h-[512px];
		transform-origin: 0 0;
	}
</style>
