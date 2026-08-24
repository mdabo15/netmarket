<script setup lang="ts">
import { PhImage, PhStar } from '@phosphor-icons/vue'
import type { ProductRead } from '~/types/api'

defineProps<{ product: ProductRead }>()

const apiBase = useApiBase()
</script>

<template>
  <NuxtLink :to="`/produits/${product.id}`" class="product-card">
    <v-card>
      <div class="product-card__image">
        <img
          v-if="product.images[0]"
          :src="resolveImageUrl(product.images[0], apiBase)"
          :alt="product.name"
          loading="lazy"
        />
        <PhImage v-else :size="28" weight="light" color="var(--color-neutral-500)" />
      </div>
      <v-card-text class="pa-2">
        <div class="product-card__name">{{ product.name }}</div>
        <div class="product-card__price">{{ formatGnf(product.price) }}</div>
        <div v-if="product.average_rating !== null" class="product-card__rating">
          <PhStar :size="11" weight="fill" color="var(--color-accent)" />
          <span>{{ product.average_rating.toFixed(1) }}</span>
          <span class="product-card__rating-count">({{ product.review_count }})</span>
        </div>
        <div class="product-card__shop">{{ product.vendor_shop_name }}</div>
      </v-card-text>
    </v-card>
  </NuxtLink>
</template>

<style scoped>
.product-card {
  text-decoration: none;
  color: inherit;
  display: block;
}

.product-card__image {
  height: 110px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-neutral-800);
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  overflow: hidden;
}

.product-card__image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-card__name {
  font-size: 12.5px;
  line-height: 1.3;
  min-height: 2.6em;
}

.product-card__price {
  font-family: var(--font-heading);
  font-size: 13px;
  font-weight: 600;
  margin-top: 4px;
}

.product-card__rating {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 10.5px;
  margin-top: 2px;
}

.product-card__rating-count {
  color: var(--color-neutral-500);
}

.product-card__shop {
  font-size: 10.5px;
  color: var(--color-neutral-500);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
