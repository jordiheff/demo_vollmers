import React from 'react'

const FLAG_STYLES = {
  missing: {
    icon: '⚠️',
    className: 'flag-missing',
    label: 'Missing'
  },
  low_confidence: {
    icon: '❓',
    className: 'flag-low-confidence',
    label: 'Uncertain'
  },
  converted: {
    icon: '🔄',
    className: 'flag-converted',
    label: 'Converted'
  },
  anomaly: {
    icon: '⚡',
    className: 'flag-anomaly',
    label: 'Check Value'
  },
  inferred: {
    icon: 'ℹ️',
    className: 'flag-inferred',
    label: 'Inferred'
  }
}

function FlagBadge({ flag }) {
  const style = FLAG_STYLES[flag.flag_type] || FLAG_STYLES.inferred

  return (
    <div className={`flag-badge ${style.className}`} title={flag.message}>
      <span className="flag-icon">{style.icon}</span>
      <span className="flag-label">{style.label}</span>
      {flag.original_value && (
        <span className="flag-original">({flag.original_value})</span>
      )}
    </div>
  )
}

export default FlagBadge
