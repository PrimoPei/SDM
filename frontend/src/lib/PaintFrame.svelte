<script lang="ts">
	import LoadingIcon from '$lib/LoadingIcon.svelte';
	import Frame from '$lib/Frame.svelte';
	import { drag } from 'd3-drag';
	import { select } from 'd3-selection';
	import { round } from '$lib/utils';

	import type { ZoomTransform } from 'd3-zoom';
	import { onMount } from 'svelte';

	import { loadingState } from '$lib/store';
	import { useMyPresence } from '$lib/liveblocks';

	const myPresence = useMyPresence();

	export let transform: ZoomTransform;
	export let color = 'black';
	export let interactive = false;

	let position = {
		x: 768,
		y: 768
	};

	let frameElement: HTMLDivElement;

	$: prompt = $myPresence?.currentPrompt;

	onMount(() => {
		function dragstarted(event: Event) {
			// console.log(event);
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
			const x = round(transform.invertX(event.x) - 512 / 2);
			const y = round(transform.invertY(event.y) - 512 / 2);

			myPresence.update({
				frame: {
					x,
					y
				}
			});
		}
		const dragHandler = drag().on('start', dragstarted).on('drag', dragged).on('end', dragended);
		select(frameElement).call(dragHandler as any);
	});
</script>

<div bind:this={frameElement}>
	<Frame {color} {position} {prompt} {transform} {interactive} />
</div>
