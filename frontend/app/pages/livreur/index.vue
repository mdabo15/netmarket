<script setup lang="ts">
import { PhQrCode } from '@phosphor-icons/vue'
import type { CourierSubOrderRead } from '~/types/api'

definePageMeta({ middleware: 'courier', layout: 'livreur' })

const { apiFetch } = useApi()
const toast = useToastStore()

const { data: deliveries, pending, refresh } = await useAsyncData(
  'courier-deliveries',
  () => apiFetch<CourierSubOrderRead[]>('/orders/courier-deliveries'),
  { default: () => [], getCachedData: () => undefined },
)

const updatingId = ref<string | null>(null)

async function markDelivered(subOrder: CourierSubOrderRead) {
  updatingId.value = subOrder.id
  try {
    await apiFetch<CourierSubOrderRead>(`/orders/sub-orders/${subOrder.id}/status`, {
      method: 'PATCH',
      body: { status: 'delivered' },
    })
    await refresh()
  } catch (e) {
    toast.error(apiErrorMessage(e, 'Impossible de mettre à jour cette livraison.'))
  } finally {
    updatingId.value = null
  }
}

const scannerOpen = ref(false)

async function handleDecode(token: string) {
  try {
    const updated = await apiFetch<CourierSubOrderRead>('/orders/sub-orders/confirm-delivery', {
      method: 'POST',
      body: { token },
    })
    await refresh()
    toast.success(`Livraison confirmée — ${shortId(updated.order_id)}.`)
  } catch (e) {
    toast.error(apiErrorMessage(e, 'QR code invalide ou expiré.'))
  }
}

function shortId(orderId: string) {
  return `#GN-${orderId.slice(0, 5).toUpperCase()}`
}
function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="app-shell pa-4" style="padding-bottom: 76px">
    <h1 class="text-h6 mb-3">Mes livraisons</h1>

    <CommonEmptyState v-if="!pending && deliveries.length === 0" message="Aucune livraison assignée pour le moment." />

    <v-card v-for="so in deliveries" :key="so.id" class="mb-3 pa-3">
      <div class="d-flex justify-space-between align-center mb-2">
        <span class="order-code">{{ shortId(so.order_id) }}</span>
        <StatusBadge :status="so.status" />
      </div>
      <div class="text-muted mb-2" style="font-size: 12px">{{ so.shop_name }} · {{ formatDate(so.created_at) }}</div>

      <div v-for="item in so.items" :key="item.id" class="d-flex justify-space-between mb-1" style="font-size: 13px">
        <span>{{ item.product_name }} × {{ item.quantity }}</span>
      </div>

      <OrderDeliveryDetails
        class="mt-3 mb-3"
        :zone="so.delivery_zone"
        :address="so.delivery_address"
        :instructions="so.delivery_instructions"
        :delivery-type="so.delivery_type"
        :recipient-name="so.recipient_name"
        :recipient-phone="so.recipient_phone"
        :pickup-point-contacts="so.pickup_point_contacts"
        :note="so.delivery_type === 'pickup_point' ? 'À déposer sur place — le client viendra le récupérer.' : null"
      />

      <v-divider class="mb-3" />

      <template v-if="so.status === 'shipped' && so.delivery_type === 'pickup_point'">
        <div v-if="so.pickup_dropoff_token" class="d-flex flex-column align-center mb-3">
          <p class="text-muted mb-2" style="font-size: 12px">Le gestionnaire du point scanne ce code à la réception</p>
          <OrderDeliveryQrCode :token="so.pickup_dropoff_token" />
        </div>
        <p class="text-muted mb-0 text-center" style="font-size: 12px">
          C'est le gestionnaire du point de retrait qui confirme la réception — rien à faire ici de votre côté.
        </p>
      </template>

      <div v-else-if="so.status === 'shipped'" class="d-flex ga-2">
        <v-btn color="primary" size="small" class="flex-grow-1" @click="scannerOpen = true">
          <PhQrCode :size="16" class="mr-1" />
          Scanner pour confirmer
        </v-btn>
        <v-btn
          variant="outlined"
          size="small"
          class="flex-grow-1"
          :loading="updatingId === so.id"
          @click="markDelivered(so)"
        >
          Marquer livrée
        </v-btn>
      </div>
    </v-card>

    <VendorQrScannerDialog v-model="scannerOpen" @decode="handleDecode" />
  </div>
</template>

<style scoped>
.order-code {
  font-family: var(--font-heading);
  font-weight: 700;
  font-size: 13.5px;
  letter-spacing: 0.01em;
  color: var(--color-accent-300);
}
</style>
