<script lang="ts">
	import { spring } from 'svelte/motion';
	import LoadingIcon from '$lib/LoadingIcon.svelte';

	import type { ZoomTransform } from 'd3-zoom';

	export let transform: ZoomTransform;
	export let color = '';
	export let position = { x: 0, y: 0 };

	// Spring animation for cursor
	const coords = spring(position, {
		stiffness: 0.07,
		damping: 0.35
	});
	// Update spring when x and y change
	$: coords.set(position);
</script>

<div
	class="frame z-0 flex relative"
	style={`transform: translateX(${$coords.x}px) translateY(${$coords.y}px) scale(${transform.k});
			background-image: linear-gradient(${color}, rgba(255,255,255,0));
			color: ${color};
	`}
>
	<LoadingIcon />
	<h2 class="text-lg">Click to paint</h2>

	<div class="absolute bottom-0 font-bold">A cat on grass</div>
</div>

<style lang="postcss" scoped>
	.frame {
		@apply pointer-events-none touch-none absolute top-0 left-0 border-2 border-sky-500 w-[512px] h-[512px];
		transform-origin: 0 0;
	}
</style>
