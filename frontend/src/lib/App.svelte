<script lang="ts">
	import Cursor from '$lib/Cursor.svelte';
	import Frame from '$lib/Frame.svelte';
	import Canvas from '$lib/Canvas.svelte';
	import Menu from '$lib/Menu.svelte';
	import type { Room } from '@liveblocks/client';
	import { COLORS, EMOJIS } from '$lib/constants';
	import { currZoomTransform, myPresence, others } from '$lib/store';

	/**
	 * The main Liveblocks code for the example.
	 * Check in src/routes/index.svelte to see the setup code.
	 */

	export let room: Room;
</script>

<!-- Show the current user's cursor location -->
<div class="text">
	{$myPresence?.cursor
		? `${$myPresence.cursor.x} × ${$myPresence.cursor.y}`
		: 'Move your cursor to broadcast its position to other people in the room.'}
</div>
<div class="fixed left-0 z-0 w-screen h-screen cursor-none">
	<Canvas />

	<main class="z-10 relative">
		{#if $myPresence?.cursor}
			<Frame color={COLORS[0]} position={$myPresence.cursor} transform={$currZoomTransform} />
			<Cursor
				emoji={EMOJIS[0]}
				color={COLORS[0]}
				position={$myPresence.cursor}
				transform={$currZoomTransform}
			/>
		{/if}

		<!-- When others connected, iterate through others and show their cursors -->
		{#if others}
			{#each [...$others] as { connectionId, presence } (connectionId)}
				{#if presence?.cursor}
					<Frame
						color={COLORS[1 + (connectionId % (COLORS.length - 1))]}
						position={presence.cursor}
						transform={$currZoomTransform}
					/>

					<Cursor
						emoji={EMOJIS[1 + (connectionId % (EMOJIS.length - 1))]}
						color={COLORS[1 + (connectionId % (COLORS.length - 1))]}
						position={presence.cursor}
						transform={$currZoomTransform}
					/>
				{/if}
			{/each}
		{/if}
	</main>
</div>
<div class="fixed bottom-0 left-0 right-0 z-50 my-2">
	<Menu />
</div>

<style lang="postcss" scoped>
</style>
