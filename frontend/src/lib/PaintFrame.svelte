<script lang="ts">
	import Frame from '$lib/Frame.svelte';
	import Move from '$lib/Icons/Move.svelte';
	import { drag } from 'd3-drag';
	import { select } from 'd3-selection';
	import { round } from '$lib/utils';

	import type { ZoomTransform } from 'd3-zoom';
	import { onMount } from 'svelte';

	import { useMyPresence } from '$lib/liveblocks';
	import { loadingState } from '$lib/store';
	const myPresence = useMyPresence();

	export let transform: ZoomTransform;
	export let color = 'black';
	export let interactive = false;

	let position = {
		x: 768,
		y: 768
	};

	let frameElement: HTMLDivElement;
	let isDragging = false;
	$: prompt = $myPresence?.currentPrompt;
	$: isLoading = $myPresence?.isLoading || false;

	let offsetX = 0;
	let offsetY = 0;
	onMount(() => {
		function dragstarted(event: Event) {
			const rect = (event.sourceEvent.target as HTMLElement).getBoundingClientRect();
			if (event.sourceEvent instanceof TouchEvent) {
				offsetX = event.sourceEvent.targetTouches[0].pageX - rect.left;
				offsetY = event.sourceEvent.targetTouches[0].pageY - rect.top;
			} else {
				offsetX = event.sourceEvent.pageX - rect.left;
				offsetY = event.sourceEvent.pageY - rect.top;
			}
			isDragging = true;
		}

		function dragged(event: Event) {
			const x = round(transform.invertX(event.x - offsetX));
			const y = round(transform.invertY(event.y - offsetY));
			position = {
				x,
				y
			};
			myPresence.update({
				cursor: {
					x: transform.invertX(event.x),
					y: transform.invertY(event.y)
				}
			});
		}

		function dragended(event: Event) {
			isDragging = false;

			const x = round(transform.invertX(event.x - offsetX));
			const y = round(transform.invertY(event.y - offsetY));

			myPresence.update({
				frame: {
					x,
					y
				}
			});
		}
		function handlePointerMove(event: PointerEvent) {
			myPresence.update({
				cursor: {
					x: transform.invertX(event.clientX),
					y: transform.invertY(event.clientY)
				}
			});
		}
		function handlePointerLeave() {
			myPresence.update({
				cursor: null
			});
		}
		const dragHandler = drag().on('start', dragstarted).on('drag', dragged).on('end', dragended);
		select(frameElement)
			.call(dragHandler as any)
			.on('pointermove', handlePointerMove)
			.on('pointerleave', handlePointerLeave);
	});
</script>

<div bind:this={frameElement}>
	<Frame
		{color}
		{position}
		loadingState={$loadingState}
		{prompt}
		{transform}
		{isLoading}
		{isDragging}
		{interactive}
	/>
</div>
