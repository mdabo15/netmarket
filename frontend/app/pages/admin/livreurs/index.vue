<script setup lang="ts">
import { PhPlus } from '@phosphor-icons/vue'
import type { CourierAdminCreate, CourierRead, CourierStatus } from '~/types/api'

definePageMeta({ middleware: 'admin', layout: 'admin' })

const { apiFetch } = useApi()
const toast = useToastStore()

const tab = ref<CourierStatus>('pending')
const tabs: { value: CourierStatus; label: string }[] = [
  { value: 'pending', label: 'En attente' },
  { value: 'approved', label: 'Approuvés' },
  { value: 'rejected', label: 'Rejetés' },
  { value: 'suspended', label: 'Suspendus' },
]

const { data: couriers, pending, refresh } = await useAsyncData(
  'admin-couriers',
  () => apiFetch<CourierRead[]>('/admin/couriers', { query: { status: tab.value } }),
  { default: () => [], getCachedData: () => undefined },
)
watch(tab, () => refresh())

const statusMeta: Record<CourierStatus, { label: string; color: string }> = {
  pending: { label: 'En attente', color: 'warning' },
  approved: { label: 'Approuvé', color: 'success' },
  rejected: { label: 'Rejeté', color: 'error' },
  suspended: { label: 'Suspendu', color: 'error' },
}

const vehicleLabels: Record<string, string> = { moto: 'Moto', taxi: 'Taxi', voiture: 'Voiture' }

// Comme pour /admin/vendeurs : la liste courante ne montre que le statut de
// l'onglet actif, donc après une action on retire l'élément localement
// plutôt que de re-filtrer côté client.
const updatingId = ref<string | null>(null)

async function update(courier: CourierRead, status: CourierStatus) {
  updatingId.value = courier.id
  try {
    await apiFetch<CourierRead>(`/admin/couriers/${courier.id}`, { method: 'PATCH', body: { status } })
    if (status !== tab.value) {
      couriers.value = couriers.value.filter((c) => c.id !== courier.id)
    } else {
      await refresh()
    }
    toast.success('Livreur mis à jour.')
  } catch (e) {
    toast.error(apiErrorMessage(e, 'Impossible de mettre à jour ce livreur.'))
  } finally {
    updatingId.value = null
  }
}

const createOpen = ref(false)
const creating = ref(false)
const form = ref({ phone: '', password: '', firstName: '', lastName: '', vehicleType: 'moto', zone: '' })
const vehicleOptions = [
  { title: 'Moto', value: 'moto' },
  { title: 'Taxi', value: 'taxi' },
  { title: 'Voiture', value: 'voiture' },
]

function resetForm() {
  form.value = { phone: '', password: '', firstName: '', lastName: '', vehicleType: 'moto', zone: '' }
}

async function createCourier() {
  if (!/^\+224\d{9}$/.test(form.value.phone.trim())) {
    toast.error('Numéro invalide — format attendu : +224XXXXXXXXX.')
    return
  }
  if (form.value.password.length < 8) {
    toast.error('Le mot de passe doit contenir au moins 8 caractères.')
    return
  }
  creating.value = true
  try {
    const payload: CourierAdminCreate = {
      phone: form.value.phone.trim(),
      password: form.value.password,
      first_name: form.value.firstName.trim() || undefined,
      last_name: form.value.lastName.trim() || undefined,
      vehicle_type: form.value.vehicleType as CourierAdminCreate['vehicle_type'],
      zone: form.value.zone.trim() || undefined,
    }
    await apiFetch<CourierRead>('/admin/couriers', { method: 'POST', body: payload })
    toast.success('Compte livreur créé et approuvé.')
    createOpen.value = false
    resetForm()
    if (tab.value === 'approved') await refresh()
    else tab.value = 'approved'
  } catch (e) {
    toast.error(apiErrorMessage(e, 'Impossible de créer ce compte livreur.'))
  } finally {
    creating.value = false
  }
}
</script>

<template>
  <div class="app-shell pa-4" style="padding-bottom: 76px">
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h6 mb-0">Livreurs</h1>
      <v-btn size="small" color="primary" variant="tonal" @click="createOpen = true">
        <PhPlus :size="16" class="mr-1" />
        Créer un compte livreur
      </v-btn>
    </div>

    <v-btn-toggle v-model="tab" mandatory density="comfortable" divided class="mb-4 flex-wrap">
      <v-btn v-for="t in tabs" :key="t.value" :value="t.value" size="small">{{ t.label }}</v-btn>
    </v-btn-toggle>

    <CommonEmptyState v-if="!pending && couriers.length === 0" message="Aucun livreur dans cette catégorie." />

    <v-card v-for="courier in couriers" :key="courier.id" class="mb-3 pa-3">
      <div class="d-flex justify-space-between align-center mb-1">
        <span style="font-weight: 600">{{ courier.full_name ?? courier.phone }}</span>
        <v-chip :color="statusMeta[courier.status].color" size="small" variant="tonal">
          {{ statusMeta[courier.status].label }}
        </v-chip>
      </div>
      <div class="text-muted mb-3" style="font-size: 12.5px">
        {{ courier.phone }} · {{ vehicleLabels[courier.vehicle_type] }}<span v-if="courier.zone"> · {{ courier.zone }}</span>
      </div>

      <div class="d-flex ga-2">
        <template v-if="courier.status === 'pending'">
          <v-btn color="primary" size="small" class="flex-grow-1" :loading="updatingId === courier.id" @click="update(courier, 'approved')">
            Approuver
          </v-btn>
          <v-btn color="error" variant="outlined" size="small" class="flex-grow-1" :loading="updatingId === courier.id" @click="update(courier, 'rejected')">
            Rejeter
          </v-btn>
        </template>
        <v-btn v-else-if="courier.status === 'approved'" color="error" variant="outlined" size="small" class="flex-grow-1" :loading="updatingId === courier.id" @click="update(courier, 'suspended')">
          Suspendre
        </v-btn>
        <v-btn v-else color="primary" size="small" class="flex-grow-1" :loading="updatingId === courier.id" @click="update(courier, 'approved')">
          Réactiver
        </v-btn>
      </div>
    </v-card>

    <v-dialog v-model="createOpen" max-width="420">
      <v-card class="pa-4">
        <h2 class="text-h6 mb-3">Créer un compte livreur</h2>
        <p class="text-muted mb-4" style="font-size: 12.5px">
          Utile pour un partenaire (entreprise de livraison, motard référencé) sans passer par l'auto-inscription.
          Le compte est approuvé immédiatement.
        </p>

        <v-form @submit.prevent="createCourier">
          <label class="field-label">Téléphone</label>
          <v-text-field v-model="form.phone" placeholder="+224621234567" class="mb-2" />

          <label class="field-label">Mot de passe</label>
          <v-text-field v-model="form.password" type="password" placeholder="8 caractères minimum" class="mb-2" />

          <div class="d-flex ga-2">
            <div class="flex-grow-1">
              <label class="field-label">Prénom (optionnel)</label>
              <v-text-field v-model="form.firstName" class="mb-2" />
            </div>
            <div class="flex-grow-1">
              <label class="field-label">Nom (optionnel)</label>
              <v-text-field v-model="form.lastName" class="mb-2" />
            </div>
          </div>

          <label class="field-label">Type de véhicule</label>
          <v-select v-model="form.vehicleType" :items="vehicleOptions" class="mb-2" />

          <label class="field-label">Zone (optionnel)</label>
          <v-text-field v-model="form.zone" placeholder="Ex: Kaloum" class="mb-3" />

          <div class="d-flex flex-column ga-2">
            <v-btn type="submit" color="primary" block :loading="creating">Créer</v-btn>
            <v-btn variant="text" block @click="createOpen = false">Annuler</v-btn>
          </div>
        </v-form>
      </v-card>
    </v-dialog>
  </div>
</template>
