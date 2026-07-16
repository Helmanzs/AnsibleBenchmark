#!/usr/bin/env bash

HOST_GROUP="local"
PROFILE=""
ANSIBLE_VERBOSITY=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -v|-vv|-vvv|-vvvv)
      ANSIBLE_VERBOSITY="$1"
      shift
      ;;
    -p|-profile)
      PROFILE="$2"
      shift 2
      ;;
    -i|-inventory)
      HOST_GROUP="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [-p <profile>] [-i <local|remote>] [-v|-vv|-vvv|-vvvv]"
      exit 1
      ;;
  esac
done

HOSTS_FILE="inventory/${HOST_GROUP}"

if [[ ! -f "$HOSTS_FILE" ]]; then
  echo "ERROR: Inventory file not found: $HOSTS_FILE"
  exit 1
fi

if [[ -z "$PROFILE" ]]; then
  echo "ERROR: No profile specified. Use -p <profile>"
  exit 1
fi

DATABASES=($(yq eval '.. | select(has("databases")) | .databases.hosts // {} | keys | .[]' "$HOSTS_FILE"))


if [[ ${#DATABASES[@]} -eq 0 ]]; then
  echo "ERROR: No databases found in $HOSTS_FILE"
  exit 1
fi


echo "Inventory:  $HOST_GROUP"
echo "Profile:    $PROFILE"
echo "Databases:  ${DATABASES[*]}"
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for db in "${DATABASES[@]}"; do
  echo ">>> Starting $db ..."
  ansible-playbook ${ANSIBLE_VERBOSITY:+"$ANSIBLE_VERBOSITY"} "$SCRIPT_DIR/setup.yml" \
    -e "target=$db" \
    -e "profile=$PROFILE" \
    -i "$HOSTS_FILE"
  echo
done

echo "All databases started."