import { writable } from 'svelte/store';
import { type ZoomTransform, zoomIdentity } from 'd3-zoom';

export const loadingState = writable<string>('');
export const currZoomTransform = writable<ZoomTransform>(zoomIdentity);
export const canvasEl = writable<HTMLCanvasElement>();
export const maskEl = writable<HTMLCanvasElement>();
export const selectedRoomID = writable<string | null>();
export const toggleAbout = writable<boolean>(false);