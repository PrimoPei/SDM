import { sveltekit } from '@sveltejs/kit/vite';
import type { UserConfig } from 'vite';

const config: UserConfig = {
	plugins: [sveltekit()],
	server: {
		// host: "0.0.0.0",
		proxy: {
			'/server': {
				target: 'http://localhost:7860',
				changeOrigin: true,
				cookieDomainRewrite: 'localhost',
				rewrite: (path) => path.replace(/^\/server/, '')
			}
		}
	}
};
export default config;
