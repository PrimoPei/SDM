<script lang="ts">
	import type { ZoomTransform } from 'd3-zoom';
	import Cursor from '$lib/Icons/Cursor.svelte';
	export let transform: ZoomTransform;
	export let color = '';
	export let emoji: string;
	export let position = { x: 0, y: 0 };

	$: coord = {
		x: transform.applyX(position.x),
		y: transform.applyY(position.y)
	};
</script>

<div
	class="cursor"
	style={`transform: translateX(${coord.x}px) translateY(${coord.y}px) scale(${transform.k});`}
>
	<Cursor classList={'block z-0 col-span-2 row-span-2'} />

	{#if emoji}
		<div
			class="absolute right-0 text-4xl col-start-2 row-start-2"
			style={`text-shadow: 0px 5px 5px ${color}`}
		>
			{emoji}
		</div>
	{/if}
</div>

<style lang="postcss" scoped>
	.cursor {
		@apply absolute top-0 left-0 grid grid-cols-3 touch-none pointer-events-none;
		transform-origin: 0 0;
	}
</style>
