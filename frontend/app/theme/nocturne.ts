/**
 * "Nocturne" dark theme — approximates the design system referenced by the
 * validated buyer-journey mockups (template_web_pwa.html), whose actual color
 * bundle wasn't available locally. Warm amber accent instead of a generic
 * SaaS blue; easy to retune by editing this file only.
 */
import type { ThemeDefinition } from 'vuetify'

export const nocturneTheme: ThemeDefinition = {
  dark: true,
  colors: {
    background: '#121214',
    // Nettement plus clair que le fond (#1A1A1D était trop proche de #121214
    // pour qu'une ombre seule se voie) — sur fond très sombre, c'est l'écart
    // de luminosité entre carte et page qui fait "lire" l'élévation, pas
    // l'ombre à elle seule.
    surface: '#222227',
    'surface-bright': '#2C2C33',
    'surface-variant': '#2C2C33',
    'on-surface-variant': '#B4B4BD',
    primary: '#E0A458',
    'primary-darken-1': '#C98A3D',
    secondary: '#8F8F99',
    error: '#E5484D',
    info: '#4C9FE0',
    success: '#3DA35D',
    warning: '#E3A008',
  },
  variables: {
    'border-color': '#FFFFFF',
    'border-opacity': 0.08,
    'high-emphasis-opacity': 0.95,
    'medium-emphasis-opacity': 0.65,
  },
}
