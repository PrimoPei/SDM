import { PUBLIC_API_BASE } from '$env/static/public';
import type { RoomResponse } from '$lib/types';
import { selectedRoomID } from '$lib/store';
import { MAX_CAPACITY } from '$lib/constants';
import type { PageLoad } from './$types';
export const prerender = true
export const ssr = false

export const load: PageLoad = async ({ url }) => {
    const roomidParam = url.searchParams.get('roomid');
    const res = await fetch(PUBLIC_API_BASE + '/rooms');
    const rooms: RoomResponse[] = await res.json();

    if (roomidParam) {
        const room = rooms.find(room => room.room_id === roomidParam);
        if (room) {
            selectedRoomID.set(roomidParam);
        }
    } else {
        const room = rooms.find(room => room.users_count < MAX_CAPACITY) || null;
        selectedRoomID.set(room ? room.room_id : null);
    }
    return { rooms };
}