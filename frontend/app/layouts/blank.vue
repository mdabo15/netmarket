<!-- No chrome: no bottom nav. Used by auth pages (connexion/inscription) and
     by "detail" pages that render their own back-arrow header inline
     (fiche produit, checkout, détail commande). -->
<template>
  <v-app>
    <v-main>
      <slot />
    </v-main>
  </v-app>
</template>
