import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://meltflake.com',
  integrations: [tailwind(), sitemap()],
  output: 'static',
  base: '/sg-charity',
});
