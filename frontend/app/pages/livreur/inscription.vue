<script setup lang="ts">
import { PhArrowLeft } from '@phosphor-icons/vue'
import type { CourierRead, VehicleType } from '~/types/api'

definePageMeta({ middleware: 'auth', layout: 'blank' })

const auth = useAuthStore()
const router = useRouter()
const { apiFetch } = useApi()
const toast = useToastStore()

if (auth.user?.role === 'courier') {
  await router.replace('/livreur')
}

const vehicleType = ref<VehicleType>('moto')
const zone = ref('')
const submitting = ref(false)

const vehicleOptions = [
  { title: 'Moto', value: 'moto' },
  { title: 'Taxi', value: 'taxi' },
  { title: 'Voiture', value: 'voiture' },
]

async function submit() {
  submitting.value = true
  try {
    await apiFetch<CourierRead>('/couriers/me', {
      method: 'POST',
      body: { vehicle_type: vehicleType.value, zone: zone.value.trim() || undefined },
    })
    await auth.fetchMe()
    toast.success('Inscription envoyée — en attente de validation par un administrateur.')
    await router.push('/livreur')
  } catch (e) {
    toast.error(apiErrorMessage(e, "Impossible de finaliser l'inscription."))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="app-shell pa-0">
    <div class="d-flex align-center pa-2 ga-2">
      <v-btn icon variant="text" @click="router.back()">
        <PhArrowLeft :size="20" />
      </v-btn>
      <h1 class="text-h6">Devenir livreur</h1>
      <LayoutHomeLink />
    </div>

    <div class="px-4 pt-2">
      <p class="text-muted mb-5" style="font-size: 13px">
        Inscris-toi comme livreur pour recevoir des sous-commandes à livrer. Ton compte devra être
        validé par un administrateur avant que des commandes te soient assignées.
      </p>

      <v-form @submit.prevent="submit">
        <label class="field-label">Type de véhicule</label>
        <v-select v-model="vehicleType" :items="vehicleOptions" class="mb-2" />

        <label class="field-label">Zone (optionnel)</label>
        <v-text-field v-model="zone" placeholder="Ex: Kaloum" class="mb-2" />

        <v-btn type="submit" color="primary" block size="large" :loading="submitting">M'inscrire</v-btn>
      </v-form>
    </div>
  </div>
</template>
