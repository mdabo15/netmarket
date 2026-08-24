<script setup lang="ts">
import QRCode from 'qrcode'

const props = defineProps<{ token: string }>()

const dataUrl = ref('')

watch(
  () => props.token,
  async (token) => {
    // Black-on-white regardless of app theme: scanners rely on raw luminance
    // contrast, and this is the one element in the app meant to be read by a
    // camera rather than a person.
    dataUrl.value = await QRCode.toDataURL(token, {
      margin: 1,
      width: 220,
      color: { dark: '#000000', light: '#ffffff' },
    })
  },
  { immediate: true },
)
</script>

<template>
  <div class="qr-card">
    <img v-if="dataUrl" :src="dataUrl" alt="QR code de confirmation de livraison" width="180" height="180" />
  </div>
</template>

<style scoped>
.qr-card {
  background: #fff;
  border-radius: var(--radius-md);
  padding: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>
