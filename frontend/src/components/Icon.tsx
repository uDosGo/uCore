import React from 'react'

export interface IconProps {
  name: string
  size?: number
  className?: string
  style?: React.CSSProperties
}

/**
 * Icon — Material Icons wrapper component.
 * Renders a Material Icons symbol using the Google Material Symbols font.
 */
export const Icon: React.FC<IconProps> = ({ name, size = 24, className, style }) => {
  const resolvedSize = Math.max(size, 24)

  return (
    <span
      className={`material-symbols-outlined ${className || ''}`}
      style={{
        fontSize: resolvedSize,
        width: resolvedSize,
        height: resolvedSize,
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        lineHeight: 1,
        userSelect: 'none',
        ...style,
      }}
      aria-hidden="true"
    >
      {name}
    </span>
  )
}

export default Icon
