<script lang="ts">
	import { zoom, zoomIdentity } from 'd3-zoom';
	import { min } from 'd3-array';
	import { select } from 'd3-selection';
	import { onMount } from 'svelte';
	import { PUBLIC_UPLOADS } from '$env/static/public';
	import {
		currZoomTransform,
		canvasEl,
		isRenderingCanvas,
		canvasSize,
		selectedRoomID
	} from '$lib/store';

	import { useMyPresence, useObject } from '$lib/liveblocks';
	import { LiveObject } from '@liveblocks/client';

	import type { PromptImgObject } from '$lib/types';
	import { FRAME_SIZE, GRID_SIZE } from '$lib/constants';
	import { PUBLIC_WS_INPAINTING } from '$env/static/public';
	import { getDefaultBackground } from '$lib/utils';

// --- 在这里加入下面这行用于调试 ---
console.log("【前端调试】正在尝试连接的 WebSocket URL 是:", PUBLIC_WS_INPAINTING);

	const myPresence = useMyPresence();
	const promptImgStorage = useObject('promptImgStorage');

	const height = $canvasSize.height;
	const width = $canvasSize.width;

	let containerEl: HTMLDivElement;
	let canvasCtx: CanvasRenderingContext2D;

	// 背景图片相关状态
	let backgroundImage: HTMLImageElement | null = null;
	let backgroundImageUrl: string | null = null;
	let isBackgroundLoaded = false;

	const imagesOnCanvas = new Set();

	function getpromptImgList(
		promptImgList: Record<string, LiveObject<PromptImgObject> | PromptImgObject>
	): PromptImgObject[] {
		if (promptImgList) {
			//sorted by last updated
			const roomid = $selectedRoomID || '';
			const canvasPixels = new Map();
			for (const x of Array.from(Array(width / GRID_SIZE).keys())) {
				for (const y of Array.from(Array(height / GRID_SIZE).keys())) {
					canvasPixels.set(`${x * GRID_SIZE}_${y * GRID_SIZE}`, null);
				}
			}

			// Object.values(promptImgList).map((e) => {
			// 	let obj;
			// 	if (e instanceof LiveObject) {
			// 		obj = e.toObject();
			// 	} else {
			// 		obj = e;
			// 	}
			// 	// const obj = promptImg.toObject();
			// 	if (obj.position) {
			// 		const key = `${obj.position.x}_${obj.position.y}`;
			// 		console.log('key', key);
			// 		const promptImgParams = {
			// 			imgURL: obj.imgURL
			// 		};
			// 		$promptImgStorage.set(key, promptImgParams);
			// 	}
			// });

			const list: PromptImgObject[] = Object.values(promptImgList)
				.map((e) => {
					if (e instanceof LiveObject) {
						return e.toObject();
					} else {
						return e;
					}
				})
				.map((e) => {
					const split_str = e.imgURL.split(/-|.jpg|.webp/);
					const date = parseInt(split_str[0]);
					const id = split_str[1];
					const [x, y] = split_str[2].split('_');
					const prompt = split_str.slice(3).join(' ');
					return {
						id,
						date,
						position: {
							x: parseInt(x),
							y: parseInt(y)
						},
						imgURL: e.imgURL,
						prompt,
						room: roomid
					};
				})
				.sort((a, b) => b.date - a.date);

			// init
			for (const promptImg of list) {
				const x = promptImg.position.x;
				const y = promptImg.position.y;
				for (const i of [...Array(FRAME_SIZE / GRID_SIZE).keys()]) {
					for (const j of [...Array(FRAME_SIZE / GRID_SIZE).keys()]) {
						const key = `${x + i * GRID_SIZE}_${y + j * GRID_SIZE}`;
						if (!canvasPixels.get(key)) {
							canvasPixels.set(key, promptImg.id);
						}
					}
				}
			}
			const ids = new Set([...canvasPixels.values()]);
			const filteredImages = list.filter((promptImg) => ids.has(promptImg.id));

			// remove images that are under other images
			list
				.filter((promptImg) => !ids.has(promptImg.id))
				.map((promptImg) => {
					const key = `${promptImg.position.x}_${promptImg.position.y}`;
					$promptImgStorage.delete(key);
					console.log('deleted', key)
				});
			return filteredImages.reverse().filter((promptImg) => !imagesOnCanvas.has(promptImg.id));
		}
		return [];
	}
	let promptImgList: PromptImgObject[] = [];
	$: promptImgList = getpromptImgList($promptImgStorage?.toObject());

	$: if (promptImgList) {
		renderImages(promptImgList);
	}

	function to_bbox(
		W: number,
		H: number,
		center: { x: number; y: number },
		w: number,
		h: number,
		margin: number
	) {
		//https://bl.ocks.org/fabiovalse/b9224bfd64ca96c47f8cdcb57b35b8e2
		const kw = (W - margin) / w;
		const kh = (H - margin) / h;
		const k = min([kw, kh]) || 1;
		const x = W / 2 - center.x * k;
		const y = H / 2 - center.y * k;
		return zoomIdentity.translate(x, y).scale(k);
	}
	onMount(async () => {
		const padding = 50;
		const scale =
			(width + padding * 2) /
			(containerEl.clientHeight > containerEl.clientWidth
				? containerEl.clientWidth
				: containerEl.clientHeight);
		const zoomHandler = zoom()
			.scaleExtent([1 / scale / 2, 3])
			// .translateExtent([
			// 	[-padding, -padding],
			// 	[width + padding, height + padding]
			// ])
			.tapDistance(10)
			.on('zoom', zoomed);

		const selection = select($canvasEl.parentElement)
			.call(zoomHandler as any)
			.call(
				zoomHandler.transform as any,
				to_bbox(
					containerEl.clientWidth,
					containerEl.clientHeight,
					{ x: width / 2, y: height / 2 },
					width,
					height,
					padding
				)
			)
			// .call(zoomHandler.scaleTo as any, 1 / scale)
			.on('pointermove', handlePointerMove)
			.on('pointerleave', handlePointerLeave);

		canvasCtx = $canvasEl.getContext('2d') as CanvasRenderingContext2D;
		
		// 加载默认背景图片
		await loadBackgroundImage();
		
		function zoomReset() {
			const scale =
				(width + padding * 2) /
				(containerEl.clientHeight > containerEl.clientWidth
					? containerEl.clientWidth
					: containerEl.clientHeight);
			zoomHandler.scaleExtent([1 / scale / 2, 3]);
			selection.call(
				zoomHandler.transform as any,
				to_bbox(
					containerEl.clientWidth,
					containerEl.clientHeight,
					{ x: width / 2, y: height / 2 },
					width,
					height,
					padding
				)
			);
		}
		window.addEventListener('resize', zoomReset);
		return () => {
			window.removeEventListener('resize', zoomReset);
		};
	});

	/**
	 * 加载默认背景图片
	 */
	async function loadBackgroundImage() {
		try {
			backgroundImageUrl = await getDefaultBackground();
			if (backgroundImageUrl) {
				backgroundImage = new Image();
				backgroundImage.crossOrigin = 'anonymous';
				backgroundImage.onload = () => {
					isBackgroundLoaded = true;
					console.log('背景图片加载成功:', backgroundImageUrl);
					// 重新渲染画布以显示背景图片
					renderCanvas();
				};
				backgroundImage.onerror = (err) => {
					console.error('背景图片加载失败:', err);
					isBackgroundLoaded = false;
				};
				backgroundImage.src = `${PUBLIC_UPLOADS}${backgroundImageUrl}`;
			}
		} catch (error) {
			console.error('获取背景图片URL失败:', error);
		}
	}

	/**
	 * 渲染画布背景图片
	 */
	function renderCanvas() {
		if (!canvasCtx) return;
		
		// 清除画布
		canvasCtx.clearRect(0, 0, width, height);
		
		// 绘制背景图片
		if (isBackgroundLoaded && backgroundImage) {
			canvasCtx.drawImage(backgroundImage, 0, 0, width, height);
		}
		
		// 重新渲染所有生成的图片
		const currentPromptImgList = getpromptImgList($promptImgStorage?.toObject());
		if (currentPromptImgList.length > 0) {
			// 清除已渲染图片的记录，以便重新绘制
			imagesOnCanvas.clear();
			renderImages(currentPromptImgList);
		}
	}

	type ImageRendered = {
		img: HTMLImageElement;
		position: { x: number; y: number };
		id: string;
	};
	async function renderImages(promptImgList: PromptImgObject[]) {
		if (!canvasCtx) return;
		
		$isRenderingCanvas = true;
		
		// 首先清除画布并绘制背景图片
		canvasCtx.clearRect(0, 0, width, height);
		if (isBackgroundLoaded && backgroundImage) {
			canvasCtx.drawImage(backgroundImage, 0, 0, width, height);
		}

		if (promptImgList.length === 0) {
			$isRenderingCanvas = false;
			return;
		}

		await Promise.allSettled(
			promptImgList.map(
				({ imgURL, position, id, room }) =>
					new Promise<ImageRendered>((resolve, reject) => {
						const img = new Image();
						img.crossOrigin = 'anonymous';
						img.onload = () => {
							const res: ImageRendered = { img, position, id };
							// 在背景图片之上绘制生成的图片
							canvasCtx.drawImage(img, position.x, position.y, img.width, img.height);
							resolve(res);
						};
						img.onerror = (err) => {
							reject(err);
						};
						img.src = `${PUBLIC_UPLOADS}/storage/${room}/${imgURL}`;
					})
			)
		).then((values) => {
			const images = values
				.filter((v) => v.status === 'fulfilled')
				.map((v) => (v as PromiseFulfilledResult<ImageRendered>).value);
			images.forEach(({ img, position, id }) => {
				// keep track of images already rendered
				//re draw in order
				imagesOnCanvas.add(id);
				canvasCtx.drawImage(img, position.x, position.y, img.width, img.height);
			});
		});
		$isRenderingCanvas = false;
	}
	function zoomed(e: Event) {
		const transform = ($currZoomTransform = e.transform);
		$canvasEl.style.transform = `translate(${transform.x}px, ${transform.y}px) scale(${transform.k})`;
	}

	// Update cursor presence to current pointer location
	function handlePointerMove(event: PointerEvent) {
		event.preventDefault();
		const x = $currZoomTransform.invertX(event.clientX);
		const y = $currZoomTransform.invertY(event.clientY);

		myPresence.update({
			cursor: {
				x,
				y
			}
		});
	}

	// When the pointer leaves the page, set cursor presence to null
	function handlePointerLeave() {
		myPresence.update({
			cursor: null
		});
	}
</script>

<div
	bind:this={containerEl}
	class="absolute top-0 left-0 right-0 bottom-0 overflow-hidden z-0 bg-blue-200"
>
	<canvas
		bind:this={$canvasEl}
		{width}
		{height}
		class="absolute top-0 left-0 bg-white shadow-2xl shadow-blue-500/20"
	/>
	<slot />
</div>

<style lang="postcss" scoped>
	canvas {
		transform-origin: 0 0;
	}
</style>
