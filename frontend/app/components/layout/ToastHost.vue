<script setup lang="ts">
const toast = useToastStore()

const current = computed(() => toast.queue[0] ?? null)

const colors: Record<string, string> = { success: 'success', error: 'error', info: 'primary' }

function close() {
  if (current.value) toast.dismiss(current.value.id)
}
</script>

<template>
  <v-snackbar
    :model-value="!!current"
    :color="current ? colors[current.type] : undefined"
    location="top"
    timeout="4000"
    class="toast-host"
    @update:model-value="(v) => !v && close()"
  >
    {{ current?.message }}
    <template #actions>
      <v-btn variant="text" size="small" @click="close">Fermer</v-btn>
    </template>
  </v-snackbar>
</template>

<style scoped>
/* Toujours au-dessus de la barre du haut / bottom nav, quel que soit le
   layout — voir components/layout/TopBar.vue et BottomNav.vue. */
.toast-host :deep(.v-snackbar__wrapper) {
  z-index: 20;
  margin-top: env(safe-area-inset-top, 0px);
}
</style>
