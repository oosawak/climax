#!/usr/bin/env bash
set -euo pipefail

# Deploy Chronicle API (Azure Functions / Python) to an existing Function App.
#
# Required env:
#   AZ_FUNCTION_APP   (e.g. func-api-eedplxgcbbmra)
#
# Optional env:
#   AZ_RESOURCE_GROUP (only used for info output)
#
# Notes:
# - This uses Azure Functions Core Tools (`func azure functionapp publish`).
# - Do NOT commit secrets. This script only deploys code.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "${ROOT_DIR}/clients/.env" ]]; then
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/clients/.env"
fi

: "${AZ_FUNCTION_APP:?missing AZ_FUNCTION_APP}"

echo "Deploying Chronicle Functions (Python) ..."
echo "  App: ${AZ_FUNCTION_APP}"
if [[ -n "${AZ_RESOURCE_GROUP:-}" ]]; then
  echo "  RG : ${AZ_RESOURCE_GROUP}"
fi

cd "${ROOT_DIR}/api/chronicle-functions-python"

func azure functionapp publish "${AZ_FUNCTION_APP}"

echo "Done."

