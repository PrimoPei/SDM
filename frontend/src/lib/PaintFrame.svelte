<script lang="ts">
	import Frame from '$lib/Frame.svelte';
	import PPButton from '$lib/Buttons/PPButton.svelte';
	import DragButton from '$lib/Buttons/DragButton.svelte';
	import MaskButton from '$lib/Buttons/MaskButton.svelte';
	import LoadingIcon from '$lib/Icons/LoadingIcon.svelte';

	import { drag } from 'd3-drag';
	import { select } from 'd3-selection';
	import { round } from '$lib/utils';

	import type { ZoomTransform } from 'd3-zoom';
	import { onMount, createEventDispatcher } from 'svelte';

	import { useMyPresence } from '$lib/liveblocks';
	import { loadingState } from '$lib/store';
	const myPresence = useMyPresence();

	const dispatch = createEventDispatcher();

	export let transform: ZoomTransform;
	export let color = 'black';
	export let interactive = false;

	let position = {
		x: 768,
		y: 768
	};

	let frameElement: HTMLDivElement;
	let dragEnabled = true;
	let isDragging = false;
	$: prompt = $myPresence?.currentPrompt;
	$: isLoading = $myPresence?.isLoading || false;

	$: coord = {
		x: transform.applyX(position.x),
		y: transform.applyY(position.y)
	};

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

	function DragMask() {
		dragEnabled = !dragEnabled;
	}
</script>

<div>
	<div
		class="absolute top-0 left-0"
		style={`transform: translateX(${coord.x}px) translateY(${coord.y}px) scale(${transform.k}); border-color: ${color}; transform-origin: 0 0;`}
	>
		<div class="frame">
			<div class="pointer-events-none touch-none">
				{#if $loadingState}
					<div class="col-span-2 row-start-1">
						<span class="text-white drop-shadow-lg">{$loadingState}</span>
					</div>
				{/if}
				{#if isLoading}
					<div class="col-start-2 row-start-2">
						<LoadingIcon />
					</div>
				{/if}

				<h2 class="text-lg">Click to paint</h2>
				<div class="absolute bottom-0 font-bold text-lg">{prompt}</div>
			</div>
			{#if !isDragging}
				<div class="absolute top-full">
					<div class="py-2">
						<PPButton on:click={() => dispatch('paintMode', { mode: 'paint' })} />
					</div>
				</div>
				<div class="absolute left-full bottom-0">
					<div class="px-2 flex flex-col gap-2">
						<DragButton isActive={dragEnabled} on:click={() => (dragEnabled = true)} />
						<MaskButton isActive={!dragEnabled} on:click={() => (dragEnabled = false)} />
					</div>
				</div>
			{/if}
		</div>
	</div>
	<div
		bind:this={frameElement}
		class="absolute top-0 left-0 w-[512px] h-[512px] border-2 border-black
		{isDragging ? 'cursor-grabbing' : 'cursor-grab'}
		{dragEnabled ? 'block' : 'hidden'}"
		style={`transform: translateX(${coord.x}px) translateY(${coord.y}px) scale(${transform.k}); border-color: ${color}; transform-origin: 0 0;`}
	/>
</div>

<style lang="postcss" scoped>
	.frame {
		@apply relative grid grid-cols-3 grid-rows-3 border-2 border-spacing-3 border-sky-500 w-[512px] h-[512px];
	}
</style>
