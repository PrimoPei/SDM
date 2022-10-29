import { writable } from 'svelte/store';
import { type ZoomTransform, zoomIdentity } from 'd3-zoom';

export const loadingState = writable<string>('');
export const currZoomTransform = writable<ZoomTransform>(zoomIdentity);
export const canvasEl = writable<HTMLCanvasElement>();
export const maskEl = writable<HTMLCanvasElement>();
export const selectedRoomID = writable<string | null>();
export const toggleAbout = writable<boolean>(false);
export const isRenderingCanvas = writable<boolean>(true);
export const showModal = writable<boolean>(false);
export const canvasSize = writable<{
    width: number;
    height: number;
}>({ width: 512 * 16, height: 512 * 16 });
