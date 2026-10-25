import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import autoprefixer from 'autoprefixer'
import tailwindcss from 'tailwindcss'
import { VitePWA } from 'vite-plugin-pwa'

const ROOT_ENV_DIR = fileURLToPath(new URL('..', import.meta.url))
const env = loadEnv('', ROOT_ENV_DIR, 'VITE_')
const publicBrand = env.VITE_PROJECT_BRAND_NAME?.trim() || 'AniLux'

export default defineConfig({
  envDir: ROOT_ENV_DIR,
  define: { 'import.meta.env.VITE_APP_BUILD_TIME': JSON.stringify(new Date().toISOString()) },
  plugins: [
    vue(),
    {
      name: 'preload-initial-route',
      apply: 'build',
      transformIndexHtml: {
        order: 'post',
        handler(html, { bundle }) {
          if (!bundle) return html;
          const names = ['AnimeView','FeedView','HomeView','OwnProfileView','UserProfileView','UserLibraryView','PlaylistsView','NotificationsView','ChatsView'];
          const routes: Record<string, { js: string[]; css: string[] }> = {};
          for (const chunk of Object.values(bundle)) {
            if (chunk.type !== 'chunk' || !names.includes(chunk.name)) continue;
            const js = new Set<string>([chunk.fileName]);
            const css = new Set<string>();
            const metadata = chunk as typeof chunk & { viteMetadata?: { importedCss?: Set<string> } };
            metadata.viteMetadata?.importedCss?.forEach(filename => css.add(filename));
            routes[chunk.name] = { js:[...js], css:[...css] };
          }
          const source = `(()=>{const routes=${JSON.stringify(routes)},p=location.pathname;const names=p==='/anime'?['AnimeView']:p==='/feed'?['FeedView']:p==='/profile'?['OwnProfileView']:p.startsWith('/profile/')?['UserProfileView']:p==='/library'?['UserLibraryView']:p==='/playlists'?['PlaylistsView']:p==='/notifications'?['NotificationsView']:p==='/chats'?['ChatsView']:p==='/'?['HomeView']:[];const seen=new Set;for(const name of names)for(const kind of ['js','css'])for(const file of routes[name]?.[kind]||[]){if(seen.has(file))continue;seen.add(file);const link=document.createElement('link');link.rel=kind==='js'?'modulepreload':'preload';if(kind==='css')link.as='style';link.href='/'+file;document.head.appendChild(link)}})()`;
          return html.replace('<head>', '<head><script>'+source+'</script>');
        },
      },
    },
    vueDevTools(),
    VitePWA({
      registerType: 'prompt',
      injectRegister: false,
      strategies: 'injectManifest',
      srcDir: 'src',
      filename: 'sw.ts',
      includeAssets: ['favicon.ico', 'pwa/*.png'],
      manifest: {
        id: '/', name: publicBrand, short_name: publicBrand,
        description: 'Каталог аниме, библиотека и общение',
        lang: 'ru-RU', start_url: '/', scope: '/',
        theme_color: '#090613', background_color: '#090613',
        display: 'standalone', display_override: ['standalone', 'minimal-ui'],
        categories: ['entertainment', 'social'],
        icons: [
          { src: '/pwa/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
          { src: '/pwa/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
          { src: '/pwa/maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
        shortcuts: [
          { name: 'Каталог', url: '/anime?section=catalog', icons: [{ src: '/pwa/icon-192.png', sizes: '192x192' }] },
          { name: 'Библиотека', url: '/library' },
          { name: 'Чаты', url: '/chats' },
        ],
      },
      injectManifest: {
        globPatterns: ['index.html', 'assets/index-*.{js,css}'],
        globIgnores: ['sakura.png'],
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024,
      },
    }),
  ],
  build: {
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('/node_modules/@ffmpeg/')) return 'vendor-ffmpeg'
          if (id.includes('/node_modules/anime4k.js/')) return 'vendor-anime4k'
          if (id.includes('/node_modules/hls.js/')) return 'vendor-hls'
          if (/\/node_modules\/(vue|vue-router|pinia|@vue\/|@tanstack\/vue-query)/.test(id)) return 'vendor-vue'
          if (/\/node_modules\/(markdown-it|dompurify|entities|linkify-it|mdurl|uc\.micro)/.test(id)) return 'vendor-content'
          if (/\/node_modules\/(axios|@unpic\/vue)/.test(id)) return 'vendor-network-ui'
          return undefined
        },
      },
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      'anime4k.js/internal/video': fileURLToPath(new URL('./node_modules/anime4k.js/dist/upscaler/video.mjs', import.meta.url)),
      'anime4k.js/internal/clamp-highlights': fileURLToPath(new URL('./node_modules/anime4k.js/dist/glsl/Restore/Anime4K_Clamp_Highlights.mjs', import.meta.url)),
      'anime4k.js/internal/restore-cnn-m': fileURLToPath(new URL('./node_modules/anime4k.js/dist/glsl/Restore/Anime4K_Restore_CNN_M.mjs', import.meta.url)),
      'anime4k.js/internal/upscale-cnn-m': fileURLToPath(new URL('./node_modules/anime4k.js/dist/glsl/Upscale/Anime4K_Upscale_CNN_x2_M.mjs', import.meta.url)),
    },
  },
  server: {
    proxy: {
      '/data/': {
        target: (env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/api$/, '').replace(/^https/, 'http'),
        changeOrigin: true,
      },
      '/media/': {
        target: (env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/api$/, '').replace(/^https/, 'http'),
        changeOrigin: true,
      },
      '/api/': {
        target: (env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/api$/, '').replace(/^https/, 'http'),
        changeOrigin: true,
      },
      '/ws/': {
        target: (env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/api$/, '').replace(/^https/, 'http'),
        ws: true,
        changeOrigin: true,
      },
    },
    allowedHosts: ['microb.taile52c1f.ts.net', 'localhost', '100.76.10.74', '127.0.0.1'],
  },
  css: {
    postcss: {
      plugins: [
        tailwindcss(),
        autoprefixer({
          overrideBrowserslist: ['> 1%', 'last 2 versions']
        })
      ],
    },
  },
})
