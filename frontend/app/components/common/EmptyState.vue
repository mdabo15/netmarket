<script setup lang="ts">
import { PhPackage } from '@phosphor-icons/vue'

withDefaults(defineProps<{ message: string; icon?: object }>(), { icon: () => PhPackage })
</script>

<template>
  <div class="empty-state">
    <component :is="icon" :size="36" weight="light" color="var(--color-neutral-500)" />
    <p class="text-muted mt-2">{{ message }}</p>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 48px 16px;
}
</style>
