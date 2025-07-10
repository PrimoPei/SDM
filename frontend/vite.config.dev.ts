import { sveltekit } from '@sveltejs/kit/vite';
import type { UserConfig } from 'vite';

const config: UserConfig = {
	plugins: [sveltekit()],
	server: {
		host: "localhost",
		proxy: {
    '/gradio': {
        target: 'http://localhost:7860',
        ws: true
    },
    '/server': {
        target: 'http://localhost:7860',
        changeOrigin: true
    }
}
	}
};
export default config;
