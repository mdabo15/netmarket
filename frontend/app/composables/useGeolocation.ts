/**
 * Thin wrapper around the browser's free Geolocation API — no map, no API
 * key, no external service. Captures a lat/lng pair to store alongside the
 * address; it complements the free-text zone/repère field, it doesn't
 * replace it (Guinean addresses are landmark-based, not formal — see
 * cahier des charges §1).
 */
export function useGeolocation() {
  const locating = ref(false)

  function locate(): Promise<{ latitude: number; longitude: number }> {
    return new Promise((resolve, reject) => {
      if (!('geolocation' in navigator)) {
        reject(new Error("La géolocalisation n'est pas disponible sur cet appareil."))
        return
      }
      locating.value = true
      navigator.geolocation.getCurrentPosition(
        (position) => {
          locating.value = false
          resolve({ latitude: position.coords.latitude, longitude: position.coords.longitude })
        },
        (err) => {
          locating.value = false
          const message =
            err.code === err.PERMISSION_DENIED
              ? "Localisation refusée — autorise l'accès à ta position dans les réglages du navigateur."
              : 'Impossible de récupérer ta position actuelle.'
          reject(new Error(message))
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
      )
    })
  }

  return { locating, locate }
}
