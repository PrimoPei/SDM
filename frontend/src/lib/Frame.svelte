<script lang="ts">
	import LoadingIcon from '$lib/Icons/LoadingIcon.svelte';

	import type { ZoomTransform } from 'd3-zoom';

	export let transform: ZoomTransform;
	export let color = '';
	export let position = { x: 0, y: 0 };
	export let prompt = '';
	export let loadingState = '';
	export let interactive = false;
	export let isDragging = false;
	export let isLoading = false;
	$: coord = {
		x: transform.applyX(position.x),
		y: transform.applyY(position.y)
	};
</script>

<div
	class="frame {isDragging ? 'cursor-grabbing' : 'cursor-grab'}"
	style={`transform: translateX(${coord.x}px) translateY(${coord.y}px) scale(${transform.k}); border-color: ${color};`}
>
	<div class={!interactive ? 'pointer-events-none touch-none' : ''}>
		{#if loadingState}
			<div class="col-span-2 row-start-1">
				<span class="text-white drop-shadow-lg">{loadingState}</span>
			</div>
		{/if}
		{#if isLoading}
			<div class="col-start-2 row-start-2">
				<LoadingIcon />
			</div>
		{/if}

		<h2 class="text-lg"></h2>
		<div class="absolute bottom-0 font-bold text-lg">{prompt}</div>
	</div>
</div>

<style lang="postcss" scoped>
	.frame {
		@apply absolute top-0 left-0  grid grid-cols-3 grid-rows-3 border-2 border-spacing-3 border-sky-500 w-[512px] h-[512px];
		transform-origin: 0 0;
	}
</style>
