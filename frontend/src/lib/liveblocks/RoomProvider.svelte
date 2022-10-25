<!--
  Works similarly to `liveblocks-react` RoomProvider
  https://liveblocks.io/docs/api-reference/liveblocks-react#RoomProvider
-->
<script lang="ts">
	// @ts-nocheck
	import { clientSymbol, roomSymbol } from './symbols';
	import type { Client, Room } from '@liveblocks/client';
	import { getContext, onDestroy, setContext } from 'svelte';
	import type { Presence } from '$lib/types';

	export let id: string;
	export let initialPresence: Presence = {};

	if (!id) {
		throw new Error('RoomProvider requires an id');
	}

	const client = getContext<Client>(clientSymbol);

	if (client) {
		const room = client.enter(id, { initialPresence });

		setContext<Room>(roomSymbol, room);

		onDestroy(() => {
			client.leave(id);
		});
	}
</script>

<slot />
