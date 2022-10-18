import { PUBLIC_API_BASE } from '$env/static/public';
import type { RoomResponse } from '$lib/types';
import { selectedRoomID } from '$lib/store';
import { MAX_CAPACITY } from '$lib/constants';

export const prerender = true
export const ssr = false
export async function load() {
    const res = await fetch(PUBLIC_API_BASE + '/rooms');
    const rooms: RoomResponse[] = await res.json();
    const room = rooms.find(room => room.users_count < MAX_CAPACITY) || null;
    selectedRoomID.set(room ? room.id : null);
    return { rooms };
}