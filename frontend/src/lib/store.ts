import { writable } from 'svelte/store';
import type { Room } from '@liveblocks/client';

import { type ZoomTransform, zoomIdentity } from 'd3-zoom';

import type {Person } from "$lib/types"

export const loadingState = writable<string>('');
export const isLoading = writable<boolean>(false);
export const isPrompting = writable<boolean>(false);
export const clickedPosition = writable<{ x: number; y: number }>();
export const showFrames = writable<boolean>(false);
export const text2img = writable<boolean>(false);

export const currZoomTransform = writable<ZoomTransform>(zoomIdentity);

