import { onDestroy } from "svelte";
import { writable, type Writable } from "svelte/store";
import { useRoom } from "./useRoom";


enum ConnectionStatus {
  "closed" = "closed",
  "authenticating" = "authenticating",
  "unavailable" = "unavailable",
  "failed" = "failed",
  "open" = "open",
  "connecting" = "connecting",
}
type TConnectionStatus = keyof typeof ConnectionStatus

export function useConnectionStatus(): Writable<TConnectionStatus> {
  const room = useRoom();
  const statusStorage = writable<TConnectionStatus>(ConnectionStatus.closed);

  const unsubscribeConnection = room.subscribe("connection", (status: TConnectionStatus) => {
    statusStorage.set(status);
  });
  onDestroy(() => {
    unsubscribeConnection();
  });

  return statusStorage;
}
