<script setup lang="ts">
const auth = useAuthStore()
const cartStore = useCartStore()

onMounted(() => {
  if (auth.isAuthenticated) cartStore.fetchCart()
})
</script>

<template>
  <v-app>
    <v-main>
      <div class="app-shell" style="padding-bottom: 76px">
        <LayoutTopBar />
        <slot />
      </div>
    </v-main>
    <LayoutBottomNav />
  </v-app>
</template>
