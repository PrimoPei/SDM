<script context="module" lang="ts">
	export const prerender = true;
</script>

<!--
	The main code for this component is in src/PixelArtTogether.svelte
	This file contains the Liveblocks providers, based on the
	liveblocks-react library
	https://liveblocks.io/docs/api-reference/liveblocks-react#LiveblocksProvider
  -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { createClient } from '@liveblocks/client';
	import type { Client } from '@liveblocks/client';
	import LiveblocksProvider from '$lib/liveblocks/LiveblocksProvider.svelte';
	import RoomProvider from '$lib/liveblocks/RoomProvider.svelte';
	import App from '$lib/App.svelte';
	import type { PageData } from './$types';
	import { PUBLIC_API_BASE } from '$env/static/public';
	import { selectedRoomID } from '$lib/store';
	export let data: PageData;

	let rooms = data.rooms;
	let loaded = false;
	let client: Client;

	$: roomId = rooms.find((room) => room.id === $selectedRoomID)?.room_id;

	$:{
		console.log("ROOM ID", $selectedRoomID);
	}
	onMount(() => {
		// document.addEventListener('wheel', (e) => e.preventDefault(), { passive: false });
		client = createClient({
			authEndpoint: PUBLIC_API_BASE + '/auth'
		});

		loaded = true;
	});
</script>

{#if loaded}
	<LiveblocksProvider {client}>
		{#if roomId}
			<RoomProvider id={roomId}>
				<App />
			</RoomProvider>
		{:else}
			<div class="flex flex-col items-center justify-center h-full">
				<h1 class="text-2xl font-bold">No room selected</h1>
				<p class="text-gray-500">Please select a room in the URL</p>
			</div>
		{/if}
	</LiveblocksProvider>
{/if}
