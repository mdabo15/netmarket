<script setup lang="ts">
import { PhHouse } from '@phosphor-icons/vue'

withDefaults(defineProps<{ to?: string }>(), { to: '/' })
</script>

<template>
  <v-btn icon variant="text" class="ml-auto" :to="to" aria-label="Accueil">
    <PhHouse :size="20" />
  </v-btn>
</template>
