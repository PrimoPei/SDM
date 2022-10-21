<script lang="ts">
	import type { ZoomTransform } from 'd3-zoom';
	import Cursor from '$lib/Icons/Cursor.svelte';
	export let transform: ZoomTransform;
	export let color = '';
	export let position = { x: 0, y: 0 };

	$: coord = {
		x: transform.applyX(position.x),
		y: transform.applyY(position.y)
	};
</script>

<div
	class="cursor text-4xl"
	style={`transform: translateX(${coord.x}px) translateY(${coord.y}px) scale(${transform.k});`}
>
	<Cursor classList={'block z-0 col-span-2 row-span-2 text-8xl'} fill={color} />
	<!-- 
	{#if emoji}
		<div
			class="absolute right-0 col-start-2 row-start-2 text-8xl"
			style={`text-shadow: 0px 5px 5px ${color}`}
		>
			{emoji}
		</div>
	{/if} -->
</div>

<style lang="postcss" scoped>
	.cursor {
		@apply absolute top-0 left-0 grid grid-cols-3 touch-none pointer-events-none;
		transform-origin: 0 0;
	}
</style>
