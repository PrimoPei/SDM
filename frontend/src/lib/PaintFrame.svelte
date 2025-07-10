<script lang="ts">
	import { PUBLIC_WS_INPAINTING } from '$env/static/public';
    // --- 这是第一条测试日志 ---
    // 如果能看到这条，说明 <script> 块本身被执行了。
    console.log("【SVELTE 脚本已执行】");

    // --- 这是第二条测试日志 ---
    // 它会告诉我们环境变量的实际值。
    console.log("【前端调试】正在尝试连接的 WebSocket URL 是:", PUBLIC_WS_INPAINTING);

    // --- 这是第三条测试日志 ---
    // onMount 是 Svelte 的一个生命周期函数，当组件成功挂载到页面上时执行。
    onMount(() => {
        console.log("【SVELTE 组件已挂载】");
    });

	import LoadingIcon from '$lib/Icons/LoadingIcon.svelte';
	import { FRAME_SIZE, GRID_SIZE } from '$lib/constants';

	import { drag } from 'd3-drag';
	import { select } from 'd3-selection';
	import { round } from '$lib/utils';

	import type { ZoomTransform } from 'd3-zoom';
	import { onMount } from 'svelte';

	import { useMyPresence } from '$lib/liveblocks';
	import { canvasEl, maskEl, loadingState, isRenderingCanvas, canvasSize } from '$lib/store';
	import { createEventDispatcher } from 'svelte';

	import { Status } from './types';
	const myPresence = useMyPresence();

	const dispatch = createEventDispatcher();

	export let transform: ZoomTransform;

	let maskCtx: CanvasRenderingContext2D;

	let position = {
		x: $canvasSize.width / 2 - FRAME_SIZE / 2,
		y: $canvasSize.height / 2 - FRAME_SIZE / 2
	};

	let frameElement: HTMLDivElement;
	let dragEnabled = true;
	let isDragging = false;
	let firstLoading: boolean | null = null;

	$: prompt = $myPresence?.currentPrompt;
	$: isLoading =
		$myPresence?.status === Status.loading || $myPresence?.status === Status.prompting || false;

	$: coord = {
		x: transform.applyX(position.x),
		y: transform.applyY(position.y)
	};

	$: if (firstLoading !== null && !$isRenderingCanvas && firstLoading) {
		cleanMask();
		firstLoading = false;
	}

	$: if ($loadingState === 'Complete' && !dragEnabled) {
		cleanMask();
		toggleDrag();
	}

	let offsetX = 0;
	let offsetY = 0;

	function cropCanvas(cursor: { x: number; y: number }) {
		maskCtx.save();
		maskCtx.clearRect(0, 0, FRAME_SIZE, FRAME_SIZE);
		maskCtx.globalCompositeOperation = 'source-over';
		maskCtx.drawImage(
			$canvasEl,
			cursor.x,
			cursor.y,
			FRAME_SIZE,
			FRAME_SIZE,
			0,
			0,
			FRAME_SIZE,
			FRAME_SIZE
		);
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
			.on('wheel', (event: WheelEvent) => {
				$canvasEl.dispatchEvent(new WheelEvent('wheel', event));
			})
			.call(dragMoveHandler() as any)
			.call(cursorUpdate);
		select($maskEl)
			.on('wheel', (event: WheelEvent) => {
				$canvasEl.dispatchEvent(new WheelEvent('wheel', event));
			})
			.call(maskingHandler() as any)
			.call(cursorUpdate);

		firstLoading = true;
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
	function constraintCursor(pos: number) {
		const x = Math.min(Math.max(pos, GRID_SIZE), FRAME_SIZE - GRID_SIZE);
		return x;
	}
	function maskingHandler() {
		let lastx: number;
		let lasty: number;
		function dragstarted(event: Event) {
			if (isLoading) return;
			const x = constraintCursor(event.x / transform.k);
			const y = constraintCursor(event.y / transform.k);
			lastx = x;
			lasty = y;
		}

		function dragged(event: Event) {
			if (isLoading) return;
			const x = constraintCursor(event.x / transform.k);
			const y = constraintCursor(event.y / transform.k);
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

			const x = round(transform.invertX(event.x - offsetX), $canvasSize);
			const y = round(transform.invertY(event.y - offsetY), $canvasSize);
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

			const x = round(transform.invertX(event.x - offsetX), $canvasSize);
			const y = round(transform.invertY(event.y - offsetY), $canvasSize);
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
		<div class="frame relative" style={`width: ${FRAME_SIZE}px;height: ${FRAME_SIZE}px;`}>
			{#if isLoading}
				<LoadingIcon classList={'absolute inset-0 m-auto animate-spin text-6xl text-black'} />
			{/if}
			{#if $myPresence?.status !== 'masking'}
				<div
					class="absolute inset-0 bg-gradient-to-t {isDragging
						? 'from-blue-700/40'
						: 'from-blue-700/90'} to-blue-500/10"
				/>
			{/if}
			<canvas
				title="Draw your mask here. The masked area will be inpainted by Stable Diffusion"
				class="{dragEnabled ? 'hidden' : 'bg-white block'} absolute top-0 left-0 z-0"
				bind:this={$maskEl}
				width={FRAME_SIZE}
				height={FRAME_SIZE}
			/>
			<div class="pointer-events-none touch-none col-span-3 z-10">
				{#if prompt}
					<div class="font-bold text-4xl text-[#387CFF] text-center px-2 line-clamp-4">
						{prompt}
					</div>
				{/if}
			</div>
			<div
				class="absolute bottom-0 origin-bottom-left"
				style={`transform: scale(${Math.max(2.5 - transform.k, 1)});`}
			>
				<!-- svelte-ignore a11y-click-events-have-key-events -->
				<div
					class="pl-3 pr-5 py-1 bg-blue-700/90 text-white text-lg xl:text-2xl rounded-tr-xl font-medium tracking-wide cursor-pointer"
					on:click={() => toggleDrag()}
					title="Enable dragging to move the frame"
				>
					{#if $loadingState !== ''}
						<div class="">
							{#if $loadingState === 'NFSW'}
								<h2 class="text-red-500 text-2xl font-bold">NSFW Alert</h2>
								<h3 class="text-red-500 text-lg">
									Possible NSFW result detected, please try again
								</h3>
							{/if}
							<p>{$loadingState}...</p>
						</div>
					{:else}
						<span class="select-none"> {dragEnabled ? '🤚 Drag me' : '🤚 Enable Drag'}</span>
					{/if}
				</div>
			</div>
			<div
				class="absolute left-full"
				style={`transform: scale(${Math.max(2.5 - transform.k, 1)}); transform-origin: 0 0;`}
			>
				{#if !isLoading}
					<div class="mx-4 flex flex-col gap-2">
						<button
							title="Click to prompt and paint"
							on:click={() => dispatch('showModal', { showModal: true })}
							class="w-10 h-10 bg-blue-600 hover:saturate-150 shadow-2xl shadow-blue-500 rounded-lg flex items-center justify-center text-3xl"
						>
							🖍
						</button>
						<button
							title="Draw your custom mask on the frame"
							on:click={toggleDrawMask}
							class="w-10 h-10 bg-blue-600 hover:saturate-200 shadow-2xl shadow-blue-500 rounded-lg flex items-center justify-center text-3xl"
						>
							<svg class="text-white" width="1em" height="1em" viewBox="0 0 100 100"
								><path
									fill="currentColor"
									d="m65.453 10.826l-.053 5c3.073.034 6.144.549 9.059 1.52l1.58-4.744a34.758 34.758 0 0 0-10.586-1.776zm-5.365.352a35.131 35.131 0 0 0-10.26 3.119l2.17 4.506a30.166 30.166 0 0 1 8.799-2.674l-.71-4.951zm20.908 3.51l-2.283 4.447a30.131 30.131 0 0 1 7.447 5.394l3.522-3.549a35.101 35.101 0 0 0-8.686-6.293zM35 19.125c-19.3 0-35 15.7-35 35s15.7 35 35 35c8.934 0 17.087-3.374 23.275-8.904c.005 0 .01 0 .014.002c.065-.059.127-.121.191-.18l.125-.115a34.677 34.677 0 0 0 2.461-2.496c.083-.092.167-.183.248-.276c.399-.455.79-.919 1.165-1.394c-.482-.04-.961-.092-1.436-.155c-.318-.041-.632-.094-.947-.146c-.158-.026-.316-.046-.473-.074a29.93 29.93 0 0 1-1.383-.283a29.851 29.851 0 0 1-1.183-.301c-.065-.018-.13-.033-.194-.051C44.234 71.216 35 59.651 35 45.875a29.876 29.876 0 0 1 9.557-21.955c.162-.151.324-.302.49-.45c.249-.22.504-.436.76-.65c.158-.131.313-.266.474-.394c.415-.332.837-.656 1.27-.965a35.075 35.075 0 0 0-2.867-.965l-.03-.008c-.287-.082-.577-.155-.867-.23c-.215-.056-.43-.118-.646-.17c-.349-.084-.701-.155-1.053-.229c-.126-.026-.25-.057-.377-.082l-.002.002A34.83 34.83 0 0 0 35 19.125zm58.2 5.928l-4.028 2.967a30.012 30.012 0 0 1 4.252 8.15l4.736-1.606a34.98 34.98 0 0 0-4.96-9.511zm6.294 14.717l-4.924.87c.536 3.029.603 6.145.194 9.19l4.955.666c.48-3.562.4-7.19-.225-10.726zM93.8 54.338a30.198 30.198 0 0 1-3.936 8.314l4.143 2.801a35.162 35.162 0 0 0 4.586-9.695l-4.793-1.42zm-6.803 11.928a29.79 29.79 0 0 1-7.213 5.687l2.451 4.358a34.776 34.776 0 0 0 8.428-6.647l-3.666-3.398zm-11.394 7.638a30.155 30.155 0 0 1-9.002 1.887l.265 4.992a35.12 35.12 0 0 0 10.498-2.199l-1.761-4.68z"
									color="currentColor"
								/></svg
							>
						</button>
					</div>
				{/if}
			</div>
		</div>
	</div>
	<div
		bind:this={frameElement}
		title={dragEnabled ? 'Drag the frame around, prompt, and paint' : 'Enable dragging'}
		class="absolute top-0 left-0 ring-8 hand
		{dragEnabled ? 'block' : 'hidden'}
		{isLoading ? 'cursor-wait' : dragEnabled ? 'block cursor-move' : 'hidden cursor-pointer'}"
		style={`width: ${FRAME_SIZE}px;height: ${FRAME_SIZE}px;transform: translateX(${coord.x}px) translateY(${coord.y}px) scale(${transform.k}); transform-origin: 0 0;`}
	/>
</div>

<style lang="postcss" scoped>
	.frame {
		@apply relative grid grid-cols-3 grid-rows-3 ring-8 ring-blue-700;
	}
</style>
