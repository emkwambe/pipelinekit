# PipelineKit Blueprint Registry

This directory contains the static files for registry.pipelinekit.dev.

## Deploy to Cloudflare Pages

1. Go to Cloudflare Dashboard → Pages → Create a project
2. Connect to github.com/emkwambe/pipelinekit
3. Build settings:
   - Build command: (none — static files)
   - Build output directory: registry
   - Root directory: /
4. Custom domain: registry.pipelinekit.dev

## Adding blueprint zips

After deploying:
1. Zip each blueprint: Compress-Archive blueprints\postgres-to-snowflake -DestinationPath registry\v1\blueprints\postgres-to-snowflake-1.0.0.zip
2. Commit and push — Cloudflare deploys automatically

## Updating the catalog

Edit registry/v1/catalog.json and push. Cloudflare deploys in ~30 seconds.
