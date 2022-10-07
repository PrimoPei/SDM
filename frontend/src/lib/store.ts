import { writable } from 'svelte/store';
import { type ZoomTransform, zoomIdentity } from 'd3-zoom';

export const loadingState = writable<string>('');
export const currZoomTransform = writable<ZoomTransform>(zoomIdentity);

