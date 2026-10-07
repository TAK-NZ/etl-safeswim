# CHANGELOG

## v1.0.0

- Initial release
- Fetches beach water quality and lifeguard patrol status from the Safeswim API
- Composite icons combining water quality colour with patrol/safety overlay badges (SafeSwim NZ iconset)
- Configurable `Show All` filter (hide GREEN/no-warning locations by default)
- Configurable `Display Mode` (combined, quality, patrol)
- Falls back to patrol-status icons for locations without a reported water quality rating
- 20 minute stale time, matching Safeswim's ~15 minute update frequency
- Update GitHub Actions to releases that run on Node.js 24, clearing the Node.js 20 deprecation warnings: `actions/checkout` v7, `actions/setup-node` v7 and `aws-actions/configure-aws-credentials` v6. `aws-actions/amazon-ecr-login` v2 already runs on Node.js 24. Not yet run in CI on these versions
- Pin the workflow runners to `ubuntu-24.04` instead of `ubuntu-latest`, so the `ubuntu-latest` migration to Ubuntu 26 (starting October 19, 2026) does not change the build environment unannounced
