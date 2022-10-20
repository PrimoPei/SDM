<script lang="ts">
	import PPButton from '$lib/Buttons/PPButton.svelte';
	import DragButton from '$lib/Buttons/DragButton.svelte';
	import MaskButton from '$lib/Buttons/MaskButton.svelte';
	import UndoButton from '$lib/Buttons/UndoButton.svelte';
	import LoadingIcon from '$lib/Icons/LoadingIcon.svelte';
	import { CANVAS_SIZE } from '$lib/constants';

	import { drag } from 'd3-drag';
	import { select } from 'd3-selection';
	import { round } from '$lib/utils';

	import type { ZoomTransform } from 'd3-zoom';
	import { onMount, createEventDispatcher } from 'svelte';

	import { useMyPresence } from '$lib/liveblocks';
	import { canvasEl, maskEl, loadingState } from '$lib/store';

	import { Status } from './types';
	const myPresence = useMyPresence();

	const dispatch = createEventDispatcher();

	export let transform: ZoomTransform;

	let maskCtx: CanvasRenderingContext2D;

	let position = {
		x: CANVAS_SIZE.width / 2 - 512 / 2,
		y: CANVAS_SIZE.height / 2 - 512 / 2
	};

	let frameElement: HTMLDivElement;
	let dragEnabled = true;
	let isDragging = false;
	$: prompt = $myPresence?.currentPrompt;
	$: isLoading =
		$myPresence?.status === Status.loading || $myPresence?.status === Status.prompting || false;

	$: {
		if (!dragEnabled && $myPresence.status === Status.loading) {
			dragEnabled = true;
		}
	}
	$: coord = {
		x: transform.applyX(position.x),
		y: transform.applyY(position.y)
	};

	let offsetX = 0;
	let offsetY = 0;

	function cropCanvas(cursor: { x: number; y: number }) {
		maskCtx.save();
		maskCtx.clearRect(0, 0, 512, 512);
		maskCtx.globalCompositeOperation = 'source-over';
		maskCtx.drawImage($canvasEl, cursor.x, cursor.y, 512, 512, 0, 0, 512, 512);
		maskCtx.restore();
	}
	function drawLine(points: { x: number; y: number; lastx: number; lasty: number }) {
		maskCtx.save();
		maskCtx.globalCompositeOperation = 'destination-out';
		maskCtx.beginPath();
		maskCtx.moveTo(points.lastx, points.lasty);
		maskCtx.lineTo(points.x, points.y);
		maskCtx.lineWidth = 50;
		maskCtx.lineCap = 'round';
		maskCtx.strokeStyle = 'black';
		maskCtx.stroke();
		maskCtx.restore();
	}
	onMount(() => {
		maskCtx = $maskEl.getContext('2d') as CanvasRenderingContext2D;

		select(frameElement)
			.call(dragMoveHandler() as any)
			.call(cursorUpdate);
		select($maskEl)
			.call(maskingHandler() as any)
			.call(cursorUpdate);
	});

	function cursorUpdate(selection: any) {
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
		return selection.on('pointermove', handlePointerMove).on('pointerleave', handlePointerLeave);
	}
	function maskingHandler() {
		let lastx: number;
		let lasty: number;
		function dragstarted(event: Event) {
			if (isLoading) return;
			const x = event.x / transform.k;
			const y = event.y / transform.k;
			lastx = x;
			lasty = y;
		}

		function dragged(event: Event) {
			if (isLoading) return;
			const x = event.x / transform.k;
			const y = event.y / transform.k;
			drawLine({ x, y, lastx, lasty });
			lastx = x;
			lasty = y;
		}

		// function dragended(event: Event) {}
		return drag().on('start', dragstarted).on('drag', dragged);
		// on('end', dragended);
	}
	function dragMoveHandler() {
		function dragstarted(event: Event) {
			if (isLoading) return;
			const rect = (event.sourceEvent.target as HTMLElement).getBoundingClientRect();

			if (typeof TouchEvent !== 'undefined' && event.sourceEvent instanceof TouchEvent) {
				offsetX = event.sourceEvent.targetTouches[0].pageX - rect.left;
				offsetY = event.sourceEvent.targetTouches[0].pageY - rect.top;
			} else if (event.sourceEvent instanceof MouseEvent) {
				offsetX = event.sourceEvent.pageX - rect.left;
				offsetY = event.sourceEvent.pageY - rect.top;
			}
			isDragging = true;
		}

		function dragged(event: Event) {
			if (isLoading) return;

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
			cropCanvas({ x, y });
		}

		function dragended(event: Event) {
			if (isLoading) return;

			isDragging = false;

			const x = round(transform.invertX(event.x - offsetX));
			const y = round(transform.invertY(event.y - offsetY));
			cropCanvas({ x, y });

			myPresence.update({
				frame: {
					x,
					y
				}
			});
		}
		return drag().on('start', dragstarted).on('drag', dragged).on('end', dragended);
	}
	function toggleDrag() {
		dragEnabled = true;
		myPresence.update({
			status: Status.dragging
		});
	}
	function toggleDrawMask() {
		dragEnabled = false;
		cropCanvas(position);
		myPresence.update({
			status: Status.masking
		});
	}

	function cleanMask() {
		cropCanvas(position);
	}
</script>

<div>
	<div
		class="absolute top-0 left-0 pen"
		style={`transform: translateX(${coord.x}px) translateY(${coord.y}px) scale(${transform.k}); transform-origin: 0 0;`}
	>
		<div class="frame">
			<canvas class={dragEnabled ? '' : 'bg-white'} bind:this={$maskEl} width="512" height="512" />
			<div class="pointer-events-none touch-none">
				{#if prompt}
					<div class="pointer-events-none touch-none">
						<div class="font-bold text-xl text-[#387CFF] text-center px-2 line-clamp-4">
							{prompt}
						</div>
					</div>
				{/if}
			</div>
			{#if isLoading}
				<div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
					<LoadingIcon classList={'animate-spin'} />
				</div>
			{/if}
			{#if !isDragging}
				<div
					class="absolute top-full"
					style={`transform: scale(${Math.max(2.5 - transform.k, 1)}); transform-origin: 0 0;`}
				>
					<div class="py-3">
						<PPButton {isLoading} on:click={() => dispatch('prompt')} />
					</div>
					{#if $loadingState !== ''}
						<div class="p-3 bg-white rounded-lg font-mono">
							{#if $loadingState === 'NFSW'}
								<h2 class="text-red-500 text-2xl font-bold">NSFW Alert</h2>
								<h3 class="text-red-500 text-lg">
									Possible NSFW result detected, please try again
								</h3>
							{/if}
							<p>{$loadingState}</p>
						</div>
					{/if}
				</div>
				<div
					class="absolute left-full"
					style={`transform: scale(${Math.max(2.5 - transform.k, 1)}); transform-origin: 0 0;`}
				>
					<div class="mx-4">
						<DragButton
							className={'p-1'}
							{isLoading}
							isActive={dragEnabled}
							on:click={toggleDrag}
						/>
						<div class="flex bg-white rounded-full mt-3 shadow-lg">
							<MaskButton
								{isLoading}
								className={'p-1'}
								isActive={!dragEnabled}
								on:click={toggleDrawMask}
							/>
							{#if !dragEnabled}
								<span class="border-gray-800 border-opacity-50 border-r-2 my-2" />
								<UndoButton className={'p-1'} {isLoading} on:click={cleanMask} />
							{/if}
						</div>
					</div>
				</div>
			{/if}
		</div>
	</div>
	<div
		bind:this={frameElement}
		class="absolute top-0 left-0 w-[512px] h-[512px] ring-8 hand
		{dragEnabled ? 'block' : 'hidden'}"
		style={`transform: translateX(${coord.x}px) translateY(${coord.y}px) scale(${transform.k}); transform-origin: 0 0;`}
	/>
</div>

<style lang="postcss" scoped>
	.frame {
		@apply relative grid grid-cols-3 grid-rows-3 ring-8 ring-[#387CFF] w-[512px] h-[512px];
	}
	.hand {
		cursor: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAAUCAYAAABvVQZ0AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAHSSURBVHgBzVQ9LENRFD4VozZWP4ku/jqJAYNoEQaWNpEwIYJFBINY6UCn6mKTKhYNSTuwVFBiaEgai9bP4CWKUftqv845vU+k7evr2C/5cu6799zvnHvOvQ+gUmEqNimEsKLZQ3YgA0j6TiNXeJPJlIZygEK1yFAmo4rj0Kkg0Jj4DyHyMxKyIt/I+zH5LJrau8V76lPMLa6KjU2vyKhZsbHl1YTX8/dX5X071eyPdX5xDRrr68BiNsNJ+AxsrS1sCf6DIEQub2hoNxJjxO7ivHnMNZqzzlHAIJBIvkBPV6cm7JC11RULWMw1LELRhwf6IPXxxSSRyMU1ztk5mKpmyX9aV0x2KUoitMHW1sxHjd3HWYQyGh7sY1+Z3ZTRMfcpCxLxHwZhZnIc63TEC3TU3iEXj2XdqGGOomKyBhxNq1fi6ZVF3J5tyK+rPGqHXmZX6OAgR61eVCc9UBDE332rzlu3uj0+WRs7GKGxoY5MWi8zZWZygp1KZUSg6yIR1RNzYQeV2/MQLC/MQqmM5HoYb8CDNl/w0GUTlpFLVDPfzi5myZ0DW3szX5Ex5whYLGYFp/pRTAEjyHcaFoX4RvqKPXRTOaJoHJDrmoKMlv0Lqhj8AlEeE/77ZUZMAAAAAElFTkSuQmCC')
				8 8,
			pointer;
	}
	.pen {
		cursor: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAExSURBVHgBnZJBjkRQEIZLt45YSIwTsLUQbuAqc4LpG3AUO9ueE5idpSFhSyKxsWCBDfKmyozZtcafVLz38r6/Sr0COCDGmEwBZ4TgB0bDfuUchvM8Z7ZtM1VVGa13m9BFuh1FEZNlmdERmfxJvryCi6JwNU2DOI4hCAJAkyVIHMe1mzCVStloS+F53lJJ0yytcA/BFKZprqXfT8FPM/u+r4ZhGJRl2ZyCkyRp0jRlfd8z13X3wyTs7oPg1YDeejeM4ghcN7quAz0ZgoC/AY7jAM/zrSRJb88M+Ov12s7zLN9ut+UAewDjOEJd18u3qqrN2eeHYfgWBMGmy1mWARnRetU0TZ9bBhecpnes4H+iVhj7AaIotoZh3DcNLMsq0MDquu6xHpKhoihf2A8LExRbBj/Uih2c7AwcBQAAAABJRU5ErkJggg==')
				8 8,
			pointer;
	}
</style>
