/**
 * Style MapLibre partagé par tous les composants carte (MapPicker,
 * PickupPointsMap...) — tuiles raster CARTO (gratuites, sans clé), voir
 * MapPicker.vue pour pourquoi on est passé de vectoriel à raster.
 */
export const MAP_RASTER_STYLE = {
  version: 8 as const,
  sources: {
    carto: {
      type: 'raster' as const,
      tiles: [
        'https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
        'https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
        'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
        'https://d.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
      ],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors © CARTO',
    },
  },
  layers: [{ id: 'carto', type: 'raster' as const, source: 'carto' }],
}

// Conakry — centre par défaut tant qu'aucune position/point n'oriente encore
// la carte.
export const MAP_DEFAULT_CENTER: [number, number] = [-13.5784, 9.6412]
export const MAP_DEFAULT_ZOOM = 13
