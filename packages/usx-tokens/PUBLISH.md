# Publishing @udos/usx-tokens

## Current Version
3.1.0

## One-Time Setup
```bash
npm login --registry https://registry.npmjs.org
# Enter your npm credentials (user: fredporter or org: udos)
```

## Publish
```bash
cd ~/Code/uCore/packages/usx-tokens
npm publish --access public
```

## After Publish (consume versioned package)
```bash
cd ~/Code/uCore
cd frontend-vue
pnpm remove @udos/usx-tokens
pnpm add @udos/usx-tokens@^3.1.0
```

Then remove the Vite alias `'@udos/usx-tokens'` from `frontend-vue/vite.config.ts` if package resolution should come only from node_modules.

## Themes Version History
| Version | Date | Changes |
|---------|------|---------|
| 3.1.0 | 2026-07-08 | Added c64, teletext, high-contrast themes from uCore |
| 3.0.0 | 2026-07-08 | Initial extraction from uCore. Added HomeNest 10-foot console additions. |