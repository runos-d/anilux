<template>
  <main class="not-found">
    <p class="code">404</p>
    <h1>Страница не найдена</h1>
    <router-link to="/">На главную</router-link>
  </main>
</template>

<style scoped>
.not-found { min-height: 60vh; display: grid; place-content: center; text-align: center; gap: 1rem; }
.code { font-size: 4rem; margin: 0; color: var(--text-secondary); }
</style>
