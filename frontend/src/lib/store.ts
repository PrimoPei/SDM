import { writable } from 'svelte/store';
import type { User } from '$lib/types';
import { browser } from '$app/environment';

export const loadingState = writable<string>('');
export const isLoading = writable<boolean>(false);

const initialUser: User = crypto.randomUUID();

export const currentUser = writable<User>(
	browser ? JSON.parse(localStorage['user'] || JSON.stringify(initialUser)) : initialUser
);
currentUser.subscribe((value) => {
	if (browser) {
		return (localStorage['user'] = JSON.stringify(value));
	}
});
