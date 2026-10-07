# CHANGELOG

## v1.1.0

- Add a `capabilities.json` manifest so CloudTAK can read the task's requirements from the image (TAK-NZ/CloudTAK#165). It declares a single required permission, `feature:submit` (the only CloudTAK API the task uses is `submit()`), 1024 MB memory / 120 s timeout, and a default `rate(15 minutes)` schedule, matching Safeswim's roughly 15 minute update frequency and the 20 minute stale time. It is validated against `StaticCapabilitiesSchema` from `@tak-ps/etl`, and a test guards it in CI
- Build and push the image with `docker buildx` in the demo and production deploy jobs, embedding `capabilities.json` as the `com.cloudtak.capabilities` OCI annotation, with `docker/setup-buildx-action@v4` providing the `docker-container` builder the annotation needs. Not verified against a registry for this repository, and it has not been checked in the demo environment
- Deliberately NOT adopting the `cloudtak-etl` CLI from `@tak-ps/etl` for the build and push: its `bin/build.ts` hardcodes the destination ECR repository as `tak-vpc-<Environment>-cloudtak-tasks`, which does not match the `<stackname>-etltasks` repository used by TAK.NZ base-infra. The existing lookup of the repository through the `EcrEtlTasksRepoArn` CloudFormation export is kept unchanged
- Add a basic test suite (`npm test`, `node:test` run through `tsx`) covering the task's static config, input and output schemas and the manifest; the `lint` script now also covers `test/`
- Use `Task.init()` for the local and Lambda entry points. No change in Lambda behaviour, `ETL_TOKEN` is always provided there
- Require Node 24 (`engines` `>= 24`), and use Node 24 in the deploy workflow's build job (it was still on Node 18), matching the Lambda base image and lint workflow
- Update dependencies: `@tak-ps/etl` 10.22.2 (minimum raised to `^10.13.0`, required for `capabilities.json`), `eslint` 10.12.0, `typescript-eslint` 8.71.1 and new dev dependency `tsx` 4.23.15. `npm audit` now reports 0 vulnerabilities (6 before, including 1 critical). `typescript` stays on 6.0.3 as `typescript-eslint` still limits supported versions to below 6.1.0
- Remove the `fast-xml-parser` override: with the updated dependencies the package is no longer in the dependency tree, so the pin had no effect
- Add a `.dockerignore` so `.git`, `.github`, `node_modules`, `dist`, `test`, `docs`, `.env*` and markdown files are kept out of the image build context. `capabilities.json`, `task.ts`, `package*.json` and `tsconfig.json` stay in the context
- The icon set release workflow (`iconset-release.yml`) is intentionally unchanged

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
