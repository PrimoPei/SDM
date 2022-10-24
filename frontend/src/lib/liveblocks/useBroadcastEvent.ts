
import { useRoom } from "./useRoom";
import type { Json, BroadcastOptions } from "@liveblocks/client";

export function useBroadcastEvent<TRoomEvent extends Json>(): (
  event: TRoomEvent,
  options?: BroadcastOptions
) => void {
  const room = useRoom();

  return (
    event: TRoomEvent,
    options: BroadcastOptions = { shouldQueueEventIfNotReady: false }
  ) => {
    room.broadcastEvent(event, options);
  }
}