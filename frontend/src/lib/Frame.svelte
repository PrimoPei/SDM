<script lang="ts">
	import LoadingIcon from '$lib/LoadingIcon.svelte';

	import type { ZoomTransform } from 'd3-zoom';

	export let transform: ZoomTransform;
	export let color = '';
	export let position = { x: 0, y: 0 };
	export let prompt = '';

	$: coord = {
		x: transform.applyX(position.x),
		y: transform.applyY(position.y)
	};
</script>

<div
	class="frame z-0 flex relative"
	style={`transform: translateX(${coord.x}px) translateY(${coord.y}px) scale(${transform.k});
			background-image: linear-gradient(${color}, rgba(255,255,255,0));
			color: ${color};
	`}
>
	<div class="small-frame z-0 flex relative" />
	<LoadingIcon />
	<h2 class="text-lg">Click to paint</h2>

	<div class="absolute bottom-0 font-bold">{prompt}}</div>
</div>

<style lang="postcss" scoped>
	.frame {
		@apply pointer-events-none touch-none absolute top-0 left-0 border-2 border-spacing-3 border-sky-500 w-[512px] h-[512px];
		transform-origin: 0 0;
	}
	.small-frame {
		@apply pointer-events-none touch-none absolute top-1/2  left-1/2 border-2 border-spacing-3 border-sky-500 w-[256px] h-[256px];
		transform: translateX(-50%) translateY(-50%);
	}
</style>
