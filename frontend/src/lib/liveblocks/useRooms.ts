import { onDestroy } from "svelte";
import { writable, type Writable } from "svelte/store";
import type { RoomResponse } from '$lib/types';
import { PUBLIC_API_BASE } from '$env/static/public';

const INTERVAL = 10000

export function useRooms(): Writable<RoomResponse[]> {
  const roomsStorage = writable<RoomResponse[]>([]);

  const interval = setInterval(
    () => {
      refreshRooms().then((rooms) => roomsStorage.set(rooms))
    }, INTERVAL);
  refreshRooms().then((rooms) => roomsStorage.set(rooms))
  onDestroy(() => {
    clearInterval(interval);
  });
  return roomsStorage
}
async function refreshRooms() {
  return fetch(PUBLIC_API_BASE + '/rooms').then((res) => res.json());
}