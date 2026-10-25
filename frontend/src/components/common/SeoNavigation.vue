<template>
  <footer class="seo-navigation" role="contentinfo" aria-label="Футер сайта">
    <nav class="seo-navigation-panel" aria-label="Разделы сайта">
      <div class="seo-navigation-heading">
        <h2><span class="logo-icon" v-html="logoSvg"></span> AniLux</h2>
        <p>Аниме, сообщество и ваша библиотека</p>
        <a :href="'mailto:' + navigation.email">{{ navigation.email }}</a>
      </div>
      <CollectionLinks :groups="navigation.groups" />
    </nav>
  </footer>
</template>
<script setup lang="ts">
import navigation from '../../../public/site-navigation.json';
import CollectionLinks from './CollectionLinks.vue';
import { logoSvg } from '@/assets/logoSvg';
</script>
<style scoped>
.seo-navigation {
  position: relative;
  width: 100%;
  box-sizing: border-box;
  margin-top: clamp(1.5rem, 1rem, 7rem);
  padding: clamp(2rem, 1vw, 3.5rem) var(--space-5) var(--space-8);
  background: transparent;
}

.seo-navigation::before {
  content: "";
  position: absolute;
  top: 0;
  left: 50%;
  width: min(calc(100% - clamp(2.5rem, 8vw, 8rem)), 1280px);
  height: 1px;
  background: var(--border-default);
  transform: translateX(-50%);
}

.seo-navigation-panel {
  display: grid;
  grid-template-columns: minmax(220px, 0.8fr) minmax(0, 3fr);
  gap: clamp(1.5rem, 3vw, 3rem);
  width: 100%;
  max-width: 1280px;
  box-sizing: border-box;
  margin: 0 auto;
  padding: clamp(1.5rem, 3vw, 2.25rem);
  overflow: hidden;
  background:
    radial-gradient(circle at 0 0, var(--accent-subtle), transparent 36%),
    var(--color-background-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.12), inset 0 1px 0 var(--border-subtle);
}

.seo-navigation-heading {
  min-width: 0;
  padding: var(--space-1) clamp(1.25rem, 3vw, 2.25rem) var(--space-1) 0;
  border-right: 1px solid var(--border-subtle);
}

.seo-navigation-heading h2 {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin: 0 0 var(--space-2);
  color: var(--text-primary);
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 650;
  letter-spacing: -0.02em;
}

.seo-navigation-heading img {
  flex: 0 0 28px;
}

.seo-navigation-heading p {
  max-width: 260px;
  margin: 0 0 var(--space-3);
  color: var(--text-tertiary);
  font-size: var(--text-sm);
  line-height: 1.55;
}

.seo-navigation-heading a {
  display: inline-flex;
  max-width: 100%;
  color: var(--text-accent);
  font-size: var(--text-sm);
  font-weight: 600;
  overflow-wrap: anywhere;
  text-decoration: none;
}

.seo-navigation-heading a:hover,
.seo-navigation-heading a:focus-visible {
  color: var(--accent-bright);
  text-decoration: underline;
  text-underline-offset: 3px;
}

@media (max-width: 1280px) {
  .seo-navigation-panel {
    grid-template-columns: 1fr;
    gap: var(--space-6);
  }

  .seo-navigation-heading {
    padding: 0 0 var(--space-5);
    border-right: 0;
    border-bottom: 1px solid var(--border-subtle);
  }
}

@media (max-width: 767px) {
  .seo-navigation {
    margin-top: clamp(3.5rem, 16vw, 5rem);
    padding: var(--space-8) var(--space-3) var(--space-5);
  }

  .seo-navigation-panel {
    gap: var(--space-5);
    padding: var(--space-4);
    border-radius: var(--radius-lg);
  }
}
</style>
