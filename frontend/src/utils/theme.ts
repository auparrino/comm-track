/**
 * Pisubí — Paleta editorial
 * Basada en la estética de auparrino.github.io/media-monitor
 * Fondo crema, texto navy, acentos con borde izquierdo.
 */

export const T = {
  // Fondos
  bg:       '#FDF0D5',   // crema cálido (fondo general)
  surface:  '#FEF9F0',   // blanco cálido (tarjetas, panels)
  surface2: '#FFF8EC',   // crema suave (filas alt, nav inactivo)

  // Texto
  text:     '#003049',   // navy profundo
  muted:    '#5C7A8A',   // slate muted
  faint:    '#8FA7B3',   // slate muy suave
  hairline: 'rgba(0, 48, 73, 0.10)',  // bordes sutiles

  // Acento principal
  blue:     '#1a6fa3',

  // Colores por commodity
  colors: {
    gold:    '#B45309',   // amber oscuro
    lithium: '#1a6fa3',   // azul
    soy:     '#2D6A4F',   // verde oscuro agrícola
    copper:  '#9A3412',   // terracota/rojizo (cobre)
    natgas:  '#0F766E',   // teal (energía)
    wheat:   '#A16207',   // ocre/dorado (trigo)
  } as Record<string, string>,

  // Colores semánticos (light mode)
  positive: '#15803d',
  negative: '#b91c1c',
  neutral:  '#5C7A8A',

  // Tipografía
  sans: "'Inter', system-ui, -apple-system, sans-serif",
  mono: "'Cascadia Code', 'Consolas', ui-monospace, monospace",
}
