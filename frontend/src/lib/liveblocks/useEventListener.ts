
import { onDestroy } from "svelte";
import { useRoom } from "./useRoom";
import type { Json } from "@liveblocks/client";

export function userEventListener<TRoomEvent extends Json>(
  callback: (eventData: { connectionId: number; event: TRoomEvent }) => void
): void {
  const room = useRoom();

  const listener = (eventData: {
    connectionId: number;
    event: TRoomEvent;
  }) => {
    callback(eventData);
  }

  const unsubscribe = room.events.customEvent.subscribe(listener);

  onDestroy(() => {
    unsubscribe();
  });
}
