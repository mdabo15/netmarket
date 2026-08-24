import type { AddressFormValues } from '~/components/address/AddressForm.vue'

/**
 * Shared by every page that saves an AddressFormValues (checkout.vue,
 * profil/adresses/nouvelle.vue, profil/adresses/[id].vue) so the rule can't
 * drift between them again — see the bug this fixed: toggling to "point de
 * retrait" without picking one from the list used to pass validation
 * whenever `zone` still held leftover text from a prior home_delivery entry
 * (nothing checked pickup_point_id itself), silently saving/submitting an
 * address that can never actually be used — checkout rejects it (409) the
 * moment it's picked, since the backend has nothing to route the order to.
 */
export function validateAddressForm(values: AddressFormValues): string | null {
  if (values.delivery_type === 'pickup_point') {
    return values.pickup_point_id ? null : 'Choisis un point de retrait dans la liste.'
  }
  const hasPosition = values.latitude !== null && values.longitude !== null
  if (!hasPosition && values.zone.trim().length < 3) {
    return 'Indique une position GPS ou décris l’endroit (au moins 3 caractères).'
  }
  return null
}
