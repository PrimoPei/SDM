<script lang="ts">
	import Room from '$lib/Icons/Room.svelte';
	import Pin from '$lib/Icons/Pin.svelte';
	import People from '$lib/Icons/People.svelte';

	export let isLoading = false;

	let rooms = [
		{ label: 'room 1', total: 11, capacity: 20 },
		{ label: 'room 2', total: 11, capacity: 20 },
		{ label: 'room 3', total: 11, capacity: 20 },
		{ label: 'room 4', total: 11, capacity: 20 },
		{ label: 'room 5', total: 11, capacity: 20 }
	];

	let selectedRoom = 0;
</script>

<button on:click disabled={isLoading} class="button-paint" title="New Paint Frame" />

<ul class="font-mono font-medium tracking-tight bg-violet-100">
	<li class="grid-row gap-2">
		<Room />
		<span> room </span>
		<People />
		<span> players </span>
	</li>
	{#each rooms as room, i}
		<li class="grid-row  gap-2">
			<span>
				{#if i === selectedRoom}
					<Pin />
				{/if}
			</span>
			<span> {room.label} </span>
			<span />
			<span>{room.total} / {room.capacity}</span>
		</li>
	{/each}
</ul>

<style lang="postcss" scoped>
	/* .button {
		@apply disabled:opacity-50 dark:bg-white dark:text-black bg-black text-white rounded-2xl text-xs shadow-sm focus:outline-none focus:border-gray-400;
	} */
	.button-paint {
		@apply text-sm font-mono bg-violet-100 text-violet-900 min-w-[25ch] flex justify-center items-center disabled:opacity-50 dark:bg-white dark:text-black rounded-2xl px-3 py-1 shadow-sm focus:outline-none focus:border-gray-400;
	}
	.grid-row {
		display: grid;
		grid-template-columns: 0.5fr 2fr 0.5fr 2fr;
		align-items: center;
		justify-items: flex-start;
	}
</style>
