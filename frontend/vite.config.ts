import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	// assetsInclude: ['**']
	resolve: {
		alias: { $assets: new URL('./src/public', import.meta.url).pathname }
	}
});
