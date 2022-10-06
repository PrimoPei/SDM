<script lang="ts">
	import LoadingIcon from '$lib/LoadingIcon.svelte';
	import { drag } from 'd3-drag';
	import { select } from 'd3-selection';
	import { round } from '$lib/utils';

	import type { ZoomTransform } from 'd3-zoom';
	import { onMount } from 'svelte';

	export let transform: ZoomTransform;
	export let color = '';

	let position = {
		x: transform.invertX(768),
		y: transform.invertX(768)
	};
	export let prompt = '';

	let frameElement: HTMLDivElement;
	$: coord = {
		x: transform.applyX(position.x),
		y: transform.applyY(position.y)
	};

	onMount(() => {
		function dragstarted(event: Event) {
			console.log(event);
		}

		function dragged(event: Event) {
			const x = round(transform.invertX(event.x) - 512 / 2);
			const y = round(transform.invertY(event.y) - 512 / 2);
			position = {
				x,
				y
			};
		}

		function dragended(event: Event) {
			console.log(event);
		}

		const dragHandler = drag().on('start', dragstarted).on('drag', dragged).on('end', dragended);
		select(frameElement).call(dragHandler as any);
	});
</script>

<div
	bind:this={frameElement}
	class="frame z-0 flex relative"
	style={`transform: translateX(${coord.x}px) translateY(${coord.y}px) scale(${transform.k});
			background-image: linear-gradient(${color}, rgba(255,255,255,0));
			color: ${color};
	`}
>
	<div class="small-frame z-0 flex relative" />
	<LoadingIcon />
	<h2 class="text-lg">Click to paint</h2>

	<div class="absolute bottom-0 font-bold">{prompt}</div>
</div>

<style lang="postcss" scoped>
	.frame {
		@apply absolute top-0 left-0 border-2 border-spacing-3 border-sky-500 w-[512px] h-[512px];
		transform-origin: 0 0;
	}
	.small-frame {
		@apply pointer-events-none touch-none absolute top-1/2  left-1/2 border-2 border-spacing-3 border-sky-500 w-[256px] h-[256px];
		transform: translateX(-50%) translateY(-50%);
	}
</style>
