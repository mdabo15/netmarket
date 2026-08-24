<script setup lang="ts">
import type { OrderStatus } from '~/types/api'

defineProps<{ status: OrderStatus }>()

const labels: Record<OrderStatus, string> = {
  pending: 'En attente',
  confirmed: 'Confirmée',
  preparing: 'En préparation',
  shipped: 'Expédiée',
  arrived_at_pickup_point: 'Arrivée au point de retrait',
  delivered: 'Livrée',
  cancelled: 'Annulée',
}

const colors: Record<OrderStatus, string> = {
  pending: 'secondary',
  confirmed: 'primary',
  preparing: 'primary',
  shipped: 'info',
  arrived_at_pickup_point: 'warning',
  delivered: 'success',
  cancelled: 'error',
}
</script>

<template>
  <v-chip :color="colors[status]" size="small" variant="tonal">{{ labels[status] }}</v-chip>
</template>
