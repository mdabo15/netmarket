<script setup lang="ts">
import { PhMotorcycle } from '@phosphor-icons/vue'
import type { CourierRead, OrderStatus, VendorSubOrderRead } from '~/types/api'

definePageMeta({ middleware: 'vendor', layout: 'vendeur' })

const { apiFetch } = useApi()
const toast = useToastStore()
const route = useRoute()
const router = useRouter()

// getCachedData: () => undefined disables Nuxt's static cross-navigation
// cache — without it, switching tabs in the vendor bottom nav and coming
// back here re-mounts the page but silently reuses the stale pre-transition
// list instead of refetching (see app/pages/vendeur/index.vue for the same fix).
const { data: subOrders, pending, refresh } = await useAsyncData(
  'vendor-sub-orders',
  () => apiFetch<VendorSubOrderRead[]>('/orders/sub-orders'),
  { default: () => [], getCachedData: () => undefined },
)

const { data: couriers } = await useAsyncData(
  'vendor-couriers',
  () => apiFetch<CourierRead[]>('/couriers'),
  { default: () => [] },
)

const courierOptions = computed(() =>
  couriers.value.map((c) => ({ title: `${c.full_name ?? c.phone} (${c.vehicle_type})`, value: c.id })),
)

const assigningId = ref<string | null>(null)
const courierSelection = ref<Record<string, string | null>>({})

function courierSelectionFor(subOrder: VendorSubOrderRead) {
  if (!(subOrder.id in courierSelection.value)) {
    courierSelection.value[subOrder.id] = subOrder.courier_id
  }
  return courierSelection.value[subOrder.id]
}

async function assignCourier(subOrder: VendorSubOrderRead) {
  const courierId = courierSelection.value[subOrder.id] ?? null
  assigningId.value = subOrder.id
  try {
    await apiFetch<VendorSubOrderRead>(`/orders/sub-orders/${subOrder.id}/courier`, {
      method: 'PATCH',
      body: { courier_id: courierId },
    })
    await refresh()
    toast.success('Livreur assigné.')
  } catch (e) {
    toast.error(apiErrorMessage(e, "Impossible d'assigner ce livreur."))
  } finally {
    assigningId.value = null
  }
}

const STATUS_FILTERS: { value: OrderStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'Toutes' },
  { value: 'pending', label: 'En attente' },
  { value: 'confirmed', label: 'Confirmée' },
  { value: 'preparing', label: 'En préparation' },
  { value: 'shipped', label: 'Expédiée' },
  { value: 'arrived_at_pickup_point', label: 'Arrivée au point' },
  { value: 'delivered', label: 'Livrée' },
  { value: 'cancelled', label: 'Annulée' },
]

// Arrivée depuis une notification ("commande reçue") : on force le filtre à
// "Toutes" (la commande neuve est "pending", déjà couvert, mais évite toute
// surprise si un jour le lien pointe vers une commande à un autre stade) et
// on scroll jusqu'à sa carte une fois la liste chargée.
const highlightOrderId = route.query.highlight as string | undefined
const statusFilter = ref<OrderStatus | 'all'>('all')
const search = ref('')

watch(
  subOrders,
  async (list) => {
    if (!highlightOrderId || list.length === 0) return
    await nextTick()
    document.getElementById(`sub-order-${highlightOrderId}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    router.replace({ query: {} })
  },
  { immediate: true },
)

const statusCounts = computed(() => {
  const counts: Record<string, number> = { all: subOrders.value.length }
  for (const so of subOrders.value) counts[so.status] = (counts[so.status] ?? 0) + 1
  return counts
})

const visible = computed(() => {
  const query = search.value.trim().toLowerCase()
  return subOrders.value.filter((so) => {
    if (statusFilter.value !== 'all' && so.status !== statusFilter.value) return false
    if (!query) return true
    return (
      shortId(so.order_id).toLowerCase().includes(query) ||
      so.items.some((item) => item.product_name.toLowerCase().includes(query))
    )
  })
})

// Mirrors backend app/orders/service.py::_ALLOWED_TRANSITIONS — the vendor
// only ever drives what happens before the parcel leaves their hands
// (accepter, préparer, expédier, annuler). Once expédiée, the vendor no
// longer has any action here : confirming receipt/remise is exclusively the
// livreur's (livraison à domicile) or the point de retrait manager's
// (retrait) job — see update_sub_order_status's is_owner_vendor guard.
const ACTIONS: Record<OrderStatus, { label: string; to: OrderStatus; color: string; variant?: 'outlined' }[]> = {
  pending: [
    { label: 'Confirmer', to: 'confirmed', color: 'primary' },
    { label: 'Refuser', to: 'cancelled', color: 'error', variant: 'outlined' },
  ],
  confirmed: [
    { label: 'Mettre en préparation', to: 'preparing', color: 'primary' },
    { label: 'Annuler', to: 'cancelled', color: 'error', variant: 'outlined' },
  ],
  preparing: [{ label: 'Marquer expédiée', to: 'shipped', color: 'primary' }],
  shipped: [],
  arrived_at_pickup_point: [],
  delivered: [],
  cancelled: [],
}

function actionsFor(so: VendorSubOrderRead) {
  return ACTIONS[so.status]
}

// Ce que le vendeur voit une fois qu'il n'a plus la main — purement
// informatif, pour qu'il comprenne qui doit agir ensuite plutôt que de se
// demander pourquoi il n'y a plus de bouton.
function waitingMessage(so: VendorSubOrderRead): string | null {
  if (so.status === 'shipped') {
    return so.delivery_type === 'pickup_point'
      ? 'En attente de dépôt au point de retrait par le livreur.'
      : 'En attente de confirmation de livraison par le livreur.'
  }
  if (so.status === 'arrived_at_pickup_point') {
    return 'En attente de remise au client par le gestionnaire du point de retrait.'
  }
  return null
}

// Un colis ne peut pas être marqué expédié sans livreur assigné pour le
// transporter (voir app/orders/service.py::update_sub_order_status, qui
// rejette la transition côté backend) — désactivé ici en plus pour ne pas
// laisser le vendeur cliquer dans le vide.
function isActionDisabled(so: VendorSubOrderRead, action: { to: OrderStatus }) {
  return action.to === 'shipped' && !so.courier_id
}

const updatingId = ref<string | null>(null)

async function transition(subOrder: VendorSubOrderRead, to: OrderStatus) {
  updatingId.value = subOrder.id
  try {
    await apiFetch<VendorSubOrderRead>(`/orders/sub-orders/${subOrder.id}/status`, {
      method: 'PATCH',
      body: { status: to },
    })
    await refresh()
  } catch (e) {
    toast.error(apiErrorMessage(e, 'Impossible de mettre à jour cette commande.'))
  } finally {
    updatingId.value = null
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
    <h1 class="text-h6 mb-3">Commandes à traiter</h1>

    <v-text-field
      v-model="search"
      placeholder="Rechercher par code ou produit…"
      density="compact"
      variant="outlined"
      hide-details
      clearable
      class="mb-3"
    />

    <div class="status-filters mb-4">
      <button
        v-for="f in STATUS_FILTERS"
        :key="f.value"
        type="button"
        class="status-filter"
        :class="{ 'status-filter--active': statusFilter === f.value }"
        @click="statusFilter = f.value"
      >
        {{ f.label }}
        <span class="status-filter__count">{{ statusCounts[f.value] ?? 0 }}</span>
      </button>
    </div>

    <CommonEmptyState v-if="!pending && visible.length === 0" message="Aucune commande ici pour le moment." />

    <v-card
      v-for="so in visible"
      :id="`sub-order-${so.order_id}`"
      :key="so.id"
      class="mb-3 pa-3"
      :class="{ 'sub-order-card--highlight': so.order_id === highlightOrderId }"
    >
      <div class="d-flex justify-space-between align-center mb-2">
        <span class="order-code">{{ shortId(so.order_id) }}</span>
        <StatusBadge :status="so.status" />
      </div>
      <div class="text-muted mb-3" style="font-size: 12px">{{ formatDate(so.created_at) }}</div>

      <div v-for="item in so.items" :key="item.id" class="d-flex justify-space-between mb-1" style="font-size: 13px">
        <span>{{ item.product_name }} × {{ item.quantity }}</span>
        <span>{{ formatGnf(item.unit_price * item.quantity) }}</span>
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
        :note="so.delivery_type === 'pickup_point' ? 'Le client viendra le récupérer en personne.' : null"
      />

      <p
        v-if="so.estimated_delivery_min && so.estimated_delivery_max && !['delivered', 'cancelled'].includes(so.status)"
        class="text-muted mb-3"
        style="font-size: 11.5px"
      >
        Estimation annoncée au client :
        <strong>{{ formatDeliveryEstimate(so.estimated_delivery_min, so.estimated_delivery_max) }}</strong>
      </p>

      <div v-if="!['delivered', 'cancelled'].includes(so.status)" class="courier-assign mb-3">
        <div class="d-flex align-center ga-1 mb-1">
          <PhMotorcycle :size="15" color="var(--color-accent)" />
          <span class="field-label mb-0">Livreur</span>
        </div>
        <div class="d-flex ga-2">
          <v-select
            :model-value="courierSelectionFor(so)"
            :items="courierOptions"
            placeholder="Non assigné"
            density="compact"
            variant="outlined"
            hide-details
            clearable
            class="flex-grow-1"
            @update:model-value="(v) => (courierSelection[so.id] = v)"
          />
          <v-btn
            size="small"
            variant="tonal"
            :loading="assigningId === so.id"
            :disabled="courierSelectionFor(so) === (so.courier_id ?? null)"
            @click="assignCourier(so)"
          >
            OK
          </v-btn>
        </div>
        <div v-if="so.courier_name" class="text-muted mt-1" style="font-size: 11.5px">
          Assigné à {{ so.courier_name }} · {{ so.courier_phone }}
        </div>
      </div>

      <v-divider class="mb-2" />

      <div class="d-flex justify-space-between mb-3" style="font-size: 13px">
        <span class="text-muted">Montant · commission {{ formatGnf(so.commission) }}</span>
        <span class="order-amount">{{ formatGnf(so.amount) }}</span>
      </div>

      <div v-if="actionsFor(so).length" class="d-flex flex-column ga-1">
        <div class="d-flex ga-2">
          <v-btn
            v-for="action in actionsFor(so)"
            :key="action.to"
            :color="action.color"
            :variant="action.variant"
            size="small"
            class="flex-grow-1"
            :loading="updatingId === so.id"
            :disabled="isActionDisabled(so, action)"
            @click="transition(so, action.to)"
          >
            {{ action.label }}
          </v-btn>
        </div>
        <span v-if="actionsFor(so).some((a) => isActionDisabled(so, a))" class="text-muted" style="font-size: 11px">
          Assignez un livreur ci-dessus avant de pouvoir marquer cette commande expédiée.
        </span>
      </div>
      <p v-else-if="waitingMessage(so)" class="text-muted mb-0" style="font-size: 12px">
        {{ waitingMessage(so) }}
      </p>
    </v-card>
  </div>
</template>

<style scoped>
.sub-order-card--highlight {
  outline: 2px solid var(--color-accent);
  animation: highlight-fade 2.5s ease-out 1;
}

@keyframes highlight-fade {
  0% {
    background: var(--color-accent-900, rgba(255, 255, 255, 0.06));
  }
  100% {
    background: transparent;
  }
}

.status-filters {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 2px;
  scrollbar-width: none;
}
.status-filters::-webkit-scrollbar {
  display: none;
}

.status-filter {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid var(--color-divider);
  background: var(--color-neutral-900);
  color: var(--color-neutral-300);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.status-filter--active {
  border-color: var(--color-accent);
  background: var(--color-accent-800);
  color: var(--color-accent-100);
}

.status-filter__count {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 999px;
  padding: 1px 6px;
  font-size: 10.5px;
}

.status-filter--active .status-filter__count {
  background: rgba(0, 0, 0, 0.25);
}

.order-code {
  font-family: var(--font-heading);
  font-weight: 700;
  font-size: 13.5px;
  letter-spacing: 0.01em;
  color: var(--color-accent-300);
}

.order-amount {
  font-family: var(--font-heading);
  font-weight: 700;
  font-size: 15px;
  color: var(--color-accent-300);
}
</style>
