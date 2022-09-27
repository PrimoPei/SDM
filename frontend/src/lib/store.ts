import { writable, get } from 'svelte/store';
import type { Room } from '@liveblocks/client';

import { type ZoomTransform, zoomIdentity } from 'd3-zoom';

export const loadingState = writable<string>('');
export const isLoading = writable<boolean>(false);
export const isPrompting = writable<boolean>(false);
export const clickedPosition = writable<{ x: number; y: number }>();

export const currZoomTransform = writable<ZoomTransform>(zoomIdentity);

export const myPresence = writable(null);
export const others = writable(null);
export const imagesList = writable(null);

export function createPresenceStore(room: Room) {
	// Get initial values for presence and others
	myPresence.set(room.getPresence());
	others.set(room.getOthers());

	const unsubscribeMyPresence = room.subscribe('my-presence', (presence) => {
		myPresence.update((_) => presence);
	});

	const unsubscribeOthers = room.subscribe('others', (otherUsers) => {
		others.update((_) => otherUsers);
	});

	myPresence.set = (presence) => {
		room.updatePresence(presence);
		return presence;
	};

	return () => {
		unsubscribeMyPresence();
		unsubscribeOthers();
	};
}

export async function createStorageStore(room: Room) {
	const { root } = await room.getStorage();

	const _imagesList = root.get('imagesList');

	imagesList.set(_imagesList);

	room.subscribe(_imagesList, () => {
		imagesList.update((_) => _imagesList);
	});
}
