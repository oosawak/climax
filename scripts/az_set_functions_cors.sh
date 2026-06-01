#!/usr/bin/env bash
set -euo pipefail

# Configure CORS for the Azure Function App so browser-hosted admin UIs
# (GitHub Pages / Static Web Apps) can call the API.
#
# Required env:
#   AZ_RESOURCE_GROUP
#   AZ_FUNCTION_APP
#
# Optional env:
#   GH_PAGES_ORIGIN (default: https://oosawak.github.io)
#   SWA_ORIGIN (default: https://gray-island-0d9f03c0f.7.azurestaticapps.net)

if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env
fi

: "${AZ_RESOURCE_GROUP:?missing AZ_RESOURCE_GROUP}"
: "${AZ_FUNCTION_APP:?missing AZ_FUNCTION_APP}"

GH_PAGES_ORIGIN="${GH_PAGES_ORIGIN:-https://oosawak.github.io}"
SWA_ORIGIN="${SWA_ORIGIN:-https://gray-island-0d9f03c0f.7.azurestaticapps.net}"

echo "Target Function App: ${AZ_FUNCTION_APP} (RG: ${AZ_RESOURCE_GROUP})"
echo "Allow origins:"
echo "  - ${GH_PAGES_ORIGIN}"
echo "  - ${SWA_ORIGIN}"

az functionapp cors add -g "${AZ_RESOURCE_GROUP}" -n "${AZ_FUNCTION_APP}" --allowed-origins "${GH_PAGES_ORIGIN}" >/dev/null
az functionapp cors add -g "${AZ_RESOURCE_GROUP}" -n "${AZ_FUNCTION_APP}" --allowed-origins "${SWA_ORIGIN}" >/dev/null

echo "Done."

