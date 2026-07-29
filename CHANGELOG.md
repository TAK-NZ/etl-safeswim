# CHANGELOG

## v1.0.0

- Initial release
- Fetches beach water quality and lifeguard patrol status from the Safeswim API
- Composite icons combining water quality colour with patrol/safety overlay badges (SafeSwim NZ iconset)
- Configurable `Show All` filter (hide GREEN/no-warning locations by default)
- Configurable `Display Mode` (combined, quality, patrol)
- Falls back to patrol-status icons for locations without a reported water quality rating
- 20 minute stale time, matching Safeswim's ~15 minute update frequency
