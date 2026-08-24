<script setup lang="ts">
import { PhArrowLeft, PhTrash } from '@phosphor-icons/vue'
import type { CategoryRead, ProductRead } from '~/types/api'
import type { ProductFormValues } from '~/components/vendor/ProductForm.vue'

definePageMeta({ middleware: 'vendor', layout: 'blank' })

const route = useRoute()
const router = useRouter()
const { apiFetch } = useApi()
const toast = useToastStore()
const productId = route.params.id as string

const { data: categories } = await useAsyncData('vendor-categories', () => apiFetch<CategoryRead[]>('/categories'), {
  default: () => [],
})
const { data: product, error: loadError } = await useAsyncData(`vendor-product-${productId}`, () =>
  apiFetch<ProductRead>(`/products/${productId}`),
)

const form = ref<ProductFormValues>({ category_id: null, name: '', description: '', price: null, stock: 0, images: [''] })
watch(
  product,
  (p) => {
    if (!p) return
    form.value = {
      category_id: p.category_id,
      name: p.name,
      description: p.description ?? '',
      price: p.price,
      stock: p.stock,
      images: p.images.length ? [...p.images] : [''],
    }
  },
  { immediate: true },
)

const submitting = ref(false)

async function submit() {
  if (!form.value.category_id || form.value.name.trim().length < 1 || form.value.price === null || form.value.price < 0) {
    toast.error('Vérifie la catégorie, le nom et le prix.')
    return
  }
  submitting.value = true
  try {
    product.value = await apiFetch<ProductRead>(`/products/${productId}`, {
      method: 'PATCH',
      body: {
        category_id: form.value.category_id,
        name: form.value.name.trim(),
        description: form.value.description.trim() || null,
        price: form.value.price,
        stock: form.value.stock ?? 0,
        images: form.value.images.map((url) => url.trim()).filter(Boolean),
      },
    })
    toast.success('Produit mis à jour.')
  } catch (e) {
    toast.error(apiErrorMessage(e, 'Impossible de sauvegarder ce produit.'))
  } finally {
    submitting.value = false
  }
}

const togglingStatus = ref(false)
async function toggleStatus(active: boolean) {
  if (!product.value) return
  togglingStatus.value = true
  try {
    product.value = await apiFetch<ProductRead>(`/products/${productId}`, {
      method: 'PATCH',
      body: { status: active ? 'active' : 'inactive' },
    })
  } catch (e) {
    toast.error(apiErrorMessage(e, 'Impossible de changer le statut du produit.'))
  } finally {
    togglingStatus.value = false
  }
}

const confirmDelete = ref(false)
const deleting = ref(false)
async function deleteProduct() {
  deleting.value = true
  try {
    await apiFetch(`/products/${productId}`, { method: 'DELETE' })
    await router.replace('/vendeur/produits')
  } catch (e) {
    toast.error(
      apiErrorMessage(
        e,
        "Impossible de supprimer ce produit — il est probablement déjà référencé dans une commande. Tu peux le désactiver à la place.",
      ),
    )
    confirmDelete.value = false
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div v-if="loadError" class="pa-6">
    <CommonEmptyState message="Produit introuvable." />
  </div>
  <div v-else class="app-shell pa-0" style="padding-bottom: 32px">
    <div class="d-flex align-center pa-2 ga-2">
      <v-btn icon variant="text" @click="router.back()">
        <PhArrowLeft :size="20" />
      </v-btn>
      <h1 class="text-h6">Modifier le produit</h1>
      <LayoutHomeLink to="/vendeur" />
    </div>

    <div v-if="product" class="px-4">
      <div class="d-flex align-center justify-space-between mb-4">
        <span style="font-size: 13px">{{ product.status === 'active' ? 'Produit actif (visible)' : 'Produit inactif (masqué)' }}</span>
        <v-switch
          :model-value="product.status === 'active'"
          color="primary"
          density="compact"
          hide-details
          :loading="togglingStatus"
          @update:model-value="toggleStatus"
        />
      </div>

      <VendorProductForm v-model="form" :categories="categories" />

      <v-btn color="primary" block size="large" class="mb-3" :loading="submitting" @click="submit">
        Enregistrer les modifications
      </v-btn>

      <v-btn variant="outlined" color="error" block @click="confirmDelete = true">
        <PhTrash :size="16" class="mr-1" />
        Supprimer le produit
      </v-btn>
    </div>

    <v-dialog v-model="confirmDelete" max-width="340">
      <v-card class="pa-5">
        <div class="text-subtitle-1 mb-2">Supprimer ce produit ?</div>
        <p class="text-muted mb-4" style="font-size: 13px">Cette action est définitive.</p>
        <div class="d-flex ga-2">
          <v-btn variant="outlined" class="flex-grow-1" @click="confirmDelete = false">Annuler</v-btn>
          <v-btn color="error" class="flex-grow-1" :loading="deleting" @click="deleteProduct">Supprimer</v-btn>
        </div>
      </v-card>
    </v-dialog>
  </div>
</template>
