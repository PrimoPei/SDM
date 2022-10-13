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

	let roomId: string;
	let loaded = false;
	let client: Client;

	onMount(() => {
		document.addEventListener('wheel', (e) => e.preventDefault(), { passive: false });

		// Add random id to room param if not set, and return the id string
		// e.g. /?room=758df70b5e94c13289df6
		roomId = 'multiplayer-SD';

		// Connect to the authentication API for Liveblocks
		client = createClient({
			publicApiKey: 'pk_test_JlUZGH3kQmhmZQiqU2l8eIi5'
		});

		loaded = true;
	});
</script>

{#if loaded}
	<!-- Provides Liveblocks hooks to children -->
	<LiveblocksProvider {client}>
		<!-- Create a room from id e.g. `sveltekit-pixel-art-758df70b5e94c13289df6` -->
		<RoomProvider id={roomId}>
			<!-- Main app component -->
			<App />
		</RoomProvider>
	</LiveblocksProvider>
{/if}
