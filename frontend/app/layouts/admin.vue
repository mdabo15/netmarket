<script setup lang="ts">
const auth = useAuthStore()
</script>

<template>
  <v-app>
    <v-main>
      <div class="app-shell" style="padding-bottom: 76px">
        <LayoutTopBar />
        <slot />
      </div>
    </v-main>
    <LayoutAdminBottomNav v-if="auth.user?.role === 'admin'" />
  </v-app>
</template>
