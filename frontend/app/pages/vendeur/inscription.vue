<script setup lang="ts">
import { PhArrowLeft } from '@phosphor-icons/vue'
import type { VendorRead } from '~/types/api'

definePageMeta({ middleware: 'auth', layout: 'blank' })

const auth = useAuthStore()
const router = useRouter()
const { apiFetch } = useApi()
const toast = useToastStore()

// Already a vendor (or came back to this page after registering) — nothing
// to do here, send them to whichever step is next.
if (auth.user?.role === 'vendor') {
  await router.replace(auth.user.email_verified ? '/vendeur' : '/vendeur/verification-email')
}

const shopName = ref('')
const zone = ref('')
const email = ref(auth.user?.email ?? '')
const submitting = ref(false)

async function submit() {
  if (shopName.value.trim().length < 2) {
    toast.error('Le nom de la boutique doit contenir au moins 2 caractères.')
    return
  }
  if (!email.value.trim().includes('@')) {
    toast.error('Indique un email valide — il sert à confirmer la création de la boutique.')
    return
  }
  submitting.value = true
  try {
    await apiFetch<VendorRead>('/vendors/me', {
      method: 'POST',
      body: { shop_name: shopName.value.trim(), zone: zone.value.trim() || undefined, email: email.value.trim() },
    })
    await auth.fetchMe()
    await router.push('/vendeur/verification-email')
  } catch (e) {
    toast.error(apiErrorMessage(e, 'Impossible de créer la boutique.'))
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
      <h1 class="text-h6">Devenir vendeur</h1>
      <LayoutHomeLink />
    </div>

    <div class="px-4 pt-2">
      <p class="text-muted mb-5" style="font-size: 13px">
        Crée ta boutique pour publier des produits sur la marketplace. Un code de vérification te sera envoyé par
        email, puis elle devra être validée par un administrateur avant que tu puisses vendre.
      </p>

      <v-form @submit.prevent="submit">
        <label class="field-label">Nom de la boutique</label>
        <v-text-field v-model="shopName" placeholder="Ex: Boutique Conakry Market" class="mb-2" />

        <label class="field-label">Zone (optionnel)</label>
        <v-text-field v-model="zone" placeholder="Ex: Kaloum" class="mb-2" />

        <label class="field-label">Email</label>
        <v-text-field v-model="email" type="email" placeholder="ex: boutique@exemple.com" class="mb-2" />

        <v-btn type="submit" color="primary" block size="large" :loading="submitting">Créer ma boutique</v-btn>
      </v-form>
    </div>
  </div>
</template>
