
import { onDestroy } from "svelte";
import { useRoom } from "./useRoom";


export function useErrorListener(callback: (err: Error) => void): void {
  const room = useRoom();

  const unsubscribe = room.events.error.subscribe((e: Error) => callback(e))

  onDestroy(() => {
    unsubscribe();
  });
}