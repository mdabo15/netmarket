<script setup lang="ts">
import { PhArrowLeft } from '@phosphor-icons/vue'
import type { CategoryRead, ProductRead } from '~/types/api'
import type { ProductFormValues } from '~/components/vendor/ProductForm.vue'

definePageMeta({ middleware: 'vendor', layout: 'blank' })

const router = useRouter()
const { apiFetch } = useApi()
const toast = useToastStore()

const { data: categories } = await useAsyncData('vendor-categories', () => apiFetch<CategoryRead[]>('/categories'), {
  default: () => [],
})

const form = ref<ProductFormValues>({ category_id: null, name: '', description: '', price: null, stock: 0, images: [''] })
const submitting = ref(false)

async function submit() {
  if (!form.value.category_id) {
    toast.error('Choisis une catégorie.')
    return
  }
  if (form.value.name.trim().length < 1) {
    toast.error('Le nom du produit est requis.')
    return
  }
  if (form.value.price === null || form.value.price < 0) {
    toast.error('Indique un prix valide.')
    return
  }

  submitting.value = true
  try {
    const product = await apiFetch<ProductRead>('/products', {
      method: 'POST',
      body: {
        category_id: form.value.category_id,
        name: form.value.name.trim(),
        description: form.value.description.trim() || undefined,
        price: form.value.price,
        stock: form.value.stock ?? 0,
        images: form.value.images.map((url) => url.trim()).filter(Boolean),
      },
    })
    toast.success('Produit publié.')
    await router.replace(`/vendeur/produits/${product.id}`)
  } catch (e) {
    toast.error(apiErrorMessage(e, 'Impossible de créer ce produit.'))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="app-shell pa-0" style="padding-bottom: 32px">
    <div class="d-flex align-center pa-2 ga-2">
      <v-btn icon variant="text" @click="router.back()">
        <PhArrowLeft :size="20" />
      </v-btn>
      <h1 class="text-h6">Nouveau produit</h1>
      <LayoutHomeLink to="/vendeur" />
    </div>

    <div class="px-4">
      <VendorProductForm v-model="form" :categories="categories" />

      <v-btn color="primary" block size="large" :loading="submitting" @click="submit">Publier le produit</v-btn>
    </div>
  </div>
</template>
