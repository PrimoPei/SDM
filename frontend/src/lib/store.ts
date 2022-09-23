import { writable } from 'svelte/store';
export const loadingState = writable<string>('');
export const isLoading = writable<boolean>(false);
