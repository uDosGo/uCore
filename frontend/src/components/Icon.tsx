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
 * Sizing is handled by usx-icons.css — inline size prop overrides only
 * when explicitly needed.
 */
export const Icon: React.FC<IconProps> = ({ name, size, className, style }) => {
  return (
    <span
      className={`material-symbols-outlined ${className || ''}`}
      style={{
        fontSize: size,
        ...style,
      }}
      aria-hidden="true"
    >
      {name}
    </span>
  )
}

export default Icon