import React, { useMemo } from 'react'
import { BORDER_MODE_CONFIGS, CHAR_H, CHAR_W, useStore } from '../GridUIStore'

export interface GridViewportMetrics {
  scale: number
  scaledCellW: number
  scaledCellH: number
  width: number
  height: number
  paddingX: number
  paddingY: number
}

export interface GridViewportWidgetProps {
  containerWidth: number
  containerHeight: number
  cols: number
  rows: number
  cellWidth?: number
  cellHeight?: number
  className?: string
  children: (metrics: GridViewportMetrics) => React.ReactNode
}

export function GridViewportWidget({
  containerWidth,
  containerHeight,
  cols,
  rows,
  cellWidth = CHAR_W,
  cellHeight = CHAR_H,
  className,
  children,
}: GridViewportWidgetProps) {
  const store = useStore()

  const metrics = useMemo<GridViewportMetrics>(() => {
    const borderCfg = BORDER_MODE_CONFIGS[store.viewport.borderMode]
    const borderPadFraction = (1 - borderCfg.fillFraction) / 2

    const availableW = containerWidth * (1 - borderPadFraction * 2)
    const availableH = containerHeight * (1 - borderPadFraction * 2)

    const contentW = cols * cellWidth
    const contentH = rows * cellHeight

    const scale = Math.min(availableW / contentW, availableH / contentH, 4)

    return {
      scale,
      scaledCellW: cellWidth * scale,
      scaledCellH: cellHeight * scale,
      width: contentW * scale,
      height: contentH * scale,
      paddingX: containerWidth * borderPadFraction,
      paddingY: containerHeight * borderPadFraction,
    }
  }, [
    store.viewport.borderMode,
    containerWidth,
    containerHeight,
    cols,
    rows,
    cellWidth,
    cellHeight,
  ])

  const displayModeStyle: React.CSSProperties =
    store.displayMode === 'mono'
      ? { filter: 'grayscale(100%)' }
      : store.displayMode === 'wireframe'
      ? { filter: 'invert(100%) contrast(200%)' }
      : { filter: 'none' }

  return (
    <div
      className={className || 'gridui-viewport-widget'}
      style={{
        width: '100%',
        height: '100%',
        padding: `${metrics.paddingY}px ${metrics.paddingX}px`,
        boxSizing: 'border-box',
      }}
    >
      <div
        style={{
          width: metrics.width,
          height: metrics.height,
          position: 'relative',
          ...displayModeStyle,
        }}
      >
        {children(metrics)}
      </div>
    </div>
  )
}
