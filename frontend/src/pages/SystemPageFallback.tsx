/* ═══════════════════════════════════════════════════════════════════
   SystemPageFallback — Dynamic Fallback for S100-S899
   ═══════════════════════════════════════════════════════════════════
   Renders fallback content for system pages that don't have
   dedicated components, showing helpful information and navigation.
   ═══════════════════════════════════════════════════════════════════ */
import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Icon } from '../components/Icon'

interface SystemPageInfo {
  code: string
  category: string
  range: string
  description: string
  relatedPages: string[]
}

// System pages registry with metadata
const SYSTEM_PAGES_INFO: Record<string, SystemPageInfo> = {
  S100: { code: 'S100', category: 'Tools', range: 'S100-S199', description: 'Tool Builder - Create and configure custom tools', relatedPages: ['S101', 'S102', 'S103'] },
  S101: { code: 'S101', category: 'Tools', range: 'S100-S199', description: 'Story Builder - Compose and manage narrative content', relatedPages: ['S100', 'S102'] },
  S102: { code: 'S102', category: 'Tools', range: 'S100-S199', description: 'Asset Manager - Organize media and resources', relatedPages: ['S100', 'S101', 'S103'] },
  S103: { code: 'S103', category: 'Tools', range: 'S100-S199', description: 'Configuration Manager - System settings and tuning', relatedPages: ['S100', 'S102'] },
  
  S110: { code: 'S110', category: 'Tools', range: 'S100-S199', description: 'Plugin Manager - Install and configure plugins', relatedPages: ['S100', 'S111', 'S112'] },
  S111: { code: 'S111', category: 'Tools', range: 'S100-S199', description: 'Extension Marketplace - Browse available extensions', relatedPages: ['S110', 'S112'] },
  S112: { code: 'S112', category: 'Tools', range: 'S100-S199', description: 'API Documentation - REST API reference', relatedPages: ['S110', 'S111'] },
  
  S200: { code: 'S200', category: 'Content', range: 'S200-S299', description: 'Content Library - Browse all content', relatedPages: ['S201', 'S202'] },
  S201: { code: 'S201', category: 'Content', range: 'S200-S299', description: 'Publishing Pipeline - Manage publication workflows', relatedPages: ['S200', 'S202', 'S203'] },
  S202: { code: 'S202', category: 'Content', range: 'S200-S299', description: 'Media Manager - Organize images, videos, files', relatedPages: ['S200', 'S201'] },
  S203: { code: 'S203', category: 'Content', range: 'S200-S299', description: 'Analytics Dashboard - Content performance metrics', relatedPages: ['S201', 'S202'] },
  
  S300: { code: 'S300', category: 'Workflows', range: 'S300-S399', description: 'Workflow Builder - Design and orchestrate workflows', relatedPages: ['S301', 'S302'] },
  S301: { code: 'S301', category: 'Workflows', range: 'S300-S399', description: 'Automation Rules - Create conditional workflows', relatedPages: ['S300', 'S302', 'S303'] },
  S302: { code: 'S302', category: 'Workflows', range: 'S300-S399', description: 'Trigger Management - Configure workflow triggers', relatedPages: ['S300', 'S301'] },
  S303: { code: 'S303', category: 'Workflows', range: 'S300-S399', description: 'Workflow History - View execution logs', relatedPages: ['S301', 'S302'] },
  
  S310: { code: 'S310', category: 'Workflows', range: 'S300-S399', description: 'Clipboard Orchestration - Manage clipboard operations', relatedPages: ['S300', 'S311'] },
  S311: { code: 'S311', category: 'Workflows', range: 'S300-S399', description: 'Data Import - Bulk import from clipboard', relatedPages: ['S310', 'S312'] },
  S312: { code: 'S312', category: 'Workflows', range: 'S300-S399', description: 'Data Export - Export to clipboard or file', relatedPages: ['S310', 'S311'] },
  
  S320: { code: 'S320', category: 'Knowledge', range: 'S300-S399', description: 'Knowledge Tools - Knowledge base management', relatedPages: ['S321', 'S322'] },
  S321: { code: 'S321', category: 'Knowledge', range: 'S300-S399', description: 'Search Index - Full-text search configuration', relatedPages: ['S320', 'S322', 'S323'] },
  S322: { code: 'S322', category: 'Knowledge', range: 'S300-S399', description: 'Entity Manager - Manage knowledge entities', relatedPages: ['S320', 'S321'] },
  S323: { code: 'S323', category: 'Knowledge', range: 'S300-S399', description: 'Graph Browser - Visualize entity relationships', relatedPages: ['S321', 'S322'] },
  
  S400: { code: 'S400', category: 'Integration', range: 'S400-S499', description: 'Integration Hub - Connect external services', relatedPages: ['S401', 'S402'] },
  S401: { code: 'S401', category: 'Integration', range: 'S400-S499', description: 'API Keys - Manage API credentials', relatedPages: ['S400', 'S402', 'S403'] },
  S402: { code: 'S402', category: 'Integration', range: 'S400-S499', description: 'Webhooks - Configure incoming webhooks', relatedPages: ['S400', 'S401'] },
  S403: { code: 'S403', category: 'Integration', range: 'S400-S499', description: 'Service Health - Monitor connected services', relatedPages: ['S401', 'S402'] },
  
  S500: { code: 'S500', category: 'Security', range: 'S500-S599', description: 'Security Hub - Access control and permissions', relatedPages: ['S501', 'S502', 'S503'] },
  S501: { code: 'S501', category: 'Security', range: 'S500-S599', description: 'User Management - Create and manage users', relatedPages: ['S500', 'S502', 'S504'] },
  S502: { code: 'S502', category: 'Security', range: 'S500-S599', description: 'Role Manager - Define role-based access', relatedPages: ['S500', 'S501', 'S503'] },
  S503: { code: 'S503', category: 'Security', range: 'S500-S599', description: 'Audit Log - View security events', relatedPages: ['S500', 'S501', 'S502'] },
  S504: { code: 'S504', category: 'Security', range: 'S500-S599', description: 'Password Policy - Configure security policies', relatedPages: ['S501', 'S502'] },
  
  S600: { code: 'S600', category: 'Learning', range: 'S600-S699', description: 'Learning Hub - Tutorials and guides (has dedicated component)', relatedPages: ['S601', 'S602'] },
  S601: { code: 'S601', category: 'Learning', range: 'S600-S699', description: 'Documentation - Official documentation', relatedPages: ['S600', 'S602', 'S603'] },
  S602: { code: 'S602', category: 'Learning', range: 'S600-S699', description: 'Tutorials - Step-by-step guides', relatedPages: ['S600', 'S601'] },
  S603: { code: 'S603', category: 'Learning', range: 'S600-S699', description: 'FAQ - Frequently asked questions', relatedPages: ['S601', 'S602'] },
  
  S700: { code: 'S700', category: 'Advanced', range: 'S700-S799', description: 'Advanced Features - Experimental capabilities', relatedPages: ['S701', 'S702'] },
  S701: { code: 'S701', category: 'Advanced', range: 'S700-S799', description: 'Performance Tuning - Optimize system performance', relatedPages: ['S700', 'S702', 'S703'] },
  S702: { code: 'S702', category: 'Advanced', range: 'S700-S799', description: 'Debug Console - Developer debugging tools', relatedPages: ['S700', 'S701'] },
  S703: { code: 'S703', category: 'Advanced', range: 'S700-S799', description: 'Feature Flags - Toggle experimental features', relatedPages: ['S701', 'S702'] },
  
  S800: { code: 'S800', category: 'System', range: 'S800-S899', description: 'System Status - Health and diagnostics', relatedPages: ['S801', 'S802', 'S803'] },
  S801: { code: 'S801', category: 'System', range: 'S800-S899', description: 'Resource Monitor - CPU, memory, disk usage', relatedPages: ['S800', 'S802', 'S804'] },
  S802: { code: 'S802', category: 'System', range: 'S800-S899', description: 'Process Manager - Running processes and threads', relatedPages: ['S800', 'S801', 'S803'] },
  S803: { code: 'S803', category: 'System', range: 'S800-S899', description: 'Log Viewer - System and application logs', relatedPages: ['S800', 'S801', 'S802'] },
  S804: { code: 'S804', category: 'System', range: 'S800-S899', description: 'Error Page - Error details and diagnostics', relatedPages: ['S800', 'S801'] },
}

interface SystemPageFallbackProps {
  pageCode: string
}

export default function SystemPageFallback({ pageCode }: SystemPageFallbackProps) {
  const navigate = useNavigate()
  const code = pageCode.toUpperCase()
  const info = SYSTEM_PAGES_INFO[code]

  if (!info) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', background: 'var(--pico-background-color, #010409)' }}>
        <Icon name="help" size={48} style={{ color: 'var(--pico-muted-color, #8b949e)', marginBottom: '16px' }} />
        <h1 style={{ margin: '0 0 8px 0' }}>Page Not Found</h1>
        <p style={{ color: 'var(--pico-muted-color, #8b949e)', marginBottom: '24px' }}>
          System page <code style={{ fontSize: '14px', background: 'var(--pico-form-element-background-color, #0d1117)', padding: '2px 6px', borderRadius: '3px' }}>{code}</code> is not registered
        </p>
        <button onClick={() => navigate('/system-tools?tab=pages')} style={{ padding: '8px 16px', background: '#58a6ff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Back to System Tools
        </button>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--pico-background-color, #010409)', padding: '40px' }}>
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '40px' }}>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '16px' }}>
            <div
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '8px',
                background: '#58a6ff20',
                color: '#58a6ff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Icon name="description" size={24} />
            </div>
            <div>
              <h1 style={{ margin: '0 0 4px 0', fontSize: '24px' }}>
                {code}
              </h1>
              <p style={{ margin: 0, fontSize: '12px', color: 'var(--pico-muted-color, #8b949e)' }}>
                {info.category} · {info.range}
              </p>
            </div>
          </div>
          <h2 style={{ margin: '0 0 12px 0', fontSize: '18px' }}>{info.description}</h2>
          <p style={{ margin: 0, color: 'var(--pico-muted-color, #8b949e)', lineHeight: '1.6' }}>
            This is a system page in the {info.category.toLowerCase()} category. It's part of the S{info.range.split('-')[1]} range of system pages.
          </p>
        </div>

        {/* Category Info */}
        <div
          style={{
            padding: '20px',
            border: '1px solid var(--pico-form-element-border-color, #30363d)',
            borderRadius: '6px',
            marginBottom: '32px',
            background: 'var(--pico-card-background-color, #0d1117)',
          }}
        >
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div>
              <h4 style={{ margin: '0 0 8px 0', fontSize: '12px', fontWeight: '600', color: 'var(--pico-muted-color, #8b949e)', textTransform: 'uppercase' }}>
                Category
              </h4>
              <p style={{ margin: 0, fontSize: '14px' }}>{info.category}</p>
            </div>
            <div>
              <h4 style={{ margin: '0 0 8px 0', fontSize: '12px', fontWeight: '600', color: 'var(--pico-muted-color, #8b949e)', textTransform: 'uppercase' }}>
                Page Range
              </h4>
              <p style={{ margin: 0, fontSize: '14px' }}>{info.range}</p>
            </div>
          </div>
        </div>

        {/* Related Pages */}
        {info.relatedPages.length > 0 && (
          <div style={{ marginBottom: '32px' }}>
            <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: '600' }}>Related Pages</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '8px' }}>
              {info.relatedPages.map((relatedCode) => {
                const relatedInfo = SYSTEM_PAGES_INFO[relatedCode]
                return (
                  <button
                    key={relatedCode}
                    onClick={() => navigate(`/s${relatedCode.slice(1).toLowerCase()}`)}
                    style={{
                      padding: '10px 12px',
                      border: '1px solid var(--pico-form-element-border-color, #30363d)',
                      borderRadius: '4px',
                      background: 'var(--pico-card-background-color, #0d1117)',
                      color: '#58a6ff',
                      cursor: 'pointer',
                      fontSize: '12px',
                      fontWeight: '500',
                      transition: 'all 200ms ease',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = '#58a6ff'
                      e.currentTarget.style.background = 'rgba(88, 166, 255, 0.1)'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'var(--pico-form-element-border-color, #30363d)'
                      e.currentTarget.style.background = 'var(--pico-card-background-color, #0d1117)'
                    }}
                  >
                    <div>{relatedCode}</div>
                    <div style={{ fontSize: '10px', color: 'var(--pico-muted-color, #8b949e)', marginTop: '4px' }}>
                      {relatedInfo?.description.split('-')[0].trim() || 'Related'}
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {/* Navigation */}
        <div style={{ display: 'flex', gap: '12px', marginTop: '32px' }}>
          <button
            onClick={() => navigate('/system-tools?tab=pages')}
            style={{
              padding: '8px 16px',
              background: '#58a6ff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: '500',
            }}
          >
            Back to System Tools
          </button>
          <button
            onClick={() => navigate('/')}
            style={{
              padding: '8px 16px',
              background: 'var(--pico-form-element-background-color, #0d1117)',
              color: 'var(--pico-muted-color, #8b949e)',
              border: '1px solid var(--pico-form-element-border-color, #30363d)',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: '500',
            }}
          >
            Home
          </button>
        </div>
      </div>
    </div>
  )
}
