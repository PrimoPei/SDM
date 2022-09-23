import { writable } from 'svelte/store';
import type { User } from '$lib/types';
import { browser } from '$app/environment';

export const loadingState = writable<string>('');
export const isLoading = writable<boolean>(false);

let initialUser: User;
if (typeof crypto['randomUUID'] === 'undefined') {
	initialUser = (1e7 + '').replace(/\d/g, (c) =>
		(c ^ (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (c / 4)))).toString(16)
	);
} else {
	initialUser = crypto.randomUUID();
}

export const currentUser = writable<User>(
	browser ? JSON.parse(localStorage['user'] || JSON.stringify(initialUser)) : initialUser
);
currentUser.subscribe((value) => {
	if (browser) {
		return (localStorage['user'] = JSON.stringify(value));
	}
});
