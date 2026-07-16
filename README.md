# AnsibleBenchmark — `Project/`

Ansible framework pro automatizované nasazení, monitoring a benchmarkování osmi databázových
systémů (ClickHouse, MariaDB, MariaDB ColumnStore, InfluxDB, Apache IoTDB, MongoDB, QuestDB,
TimescaleDB) v izolovaných LXD kontejnerech. Vznikl jako praktická část diplomové práce
(viz `../Thesis/`).

- Každý databázový systém běží ve **vlastním LXD kontejneru** s přiděleným CPU/RAM/diskem.
- Vytváření a mazání kontejnerů řídí Ansible (modul `community.general.lxd_container`) —
  spouští se **lokálně na stroji, kde běží LXD daemon** (skupina inventáře `servers`).
- Do každého kontejneru se při vytvoření nainstaluje daná databáze + `node_exporter`.
- Samostatný kontejner běží pro **monitoring** — Prometheus (sběr metrik) + Grafana
  (vizualizace, anotace jednotlivých testovacích běhů).
- Benchmark testy (insert, single_point, condition, aggregate, live_insert) se spouští přes
  Ansible playbook `tests/test.yml`, výsledky se ukládají jako NDJSON do `results/`.

## Struktura adresáře

```text
Project/
├── ansible.cfg               # konfigurace Ansible
├── inventory/                # inventáře + group_vars
│   └── group_vars/
├── roles/                    # role pro každou DB + common-create/start/stop/delete, monitoring, node-exporter...
├── setup/                    # playbooky pro (de)provisioning kontejnerů a monitoringu
├── tests/                    # testovací playbooky + python driver skripty pro live_insert test
├── tools/                    # run_test.sh, run_live_insert.sh — vstupní CLI skripty
├── vars/                     # resource_profiles.yml, test_types.yml
└── results/                  # výstupní *.ndjson soubory s výsledky benchmarků
```

## Požadavky

**Řídicí stroj**:

- Linux s nainstalovaným **LXD** (`snap install lxd`) a inicializovaným
  `lxd init` (bridge nutný).
- **Ansible ≥ 2.16**
- Ansible kolekce **`community.general`** (modul `lxd_container`) a dále
  `community.mysql`, `community.mongodb`, `community.postgresql`
- **Python 3**
- **`yq`** (`tools/run_test.sh` a `tools/run_live_insert.sh` k parsování inventáře a profilů)
- SSH klíč — veřejný klíč se automaticky vkládá do cloud-init každého nově vytvořeného kontejneru

## Instalace

```bash
git clone https://github.com/Helmanzs/AnsibleBenchmark.git
cd AnsibleBenchmark/Project

# Ansible + LXD (příklad pro Ubuntu)
sudo apt update
sudo apt install -y ansible lxd
sudo lxd init

# Ansible kolekce
ansible-galaxy collection install community.general community.mysql community.mongodb community.postgresql

# SSH klíč pro přístup do kontejnerů
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519

# yq
sudo snap install yq
```

## Konfigurace inventáře

Výchozí inventory soubor podle `ansible.cfg` je `inventory/local`. Inventář má tři skupiny:

- **`databases`** — jeden host pro každý testovaný systém, se statickou IP adresou v LXD síti,
  připojení přes SSH.
- **`monitoring`** — host `grafana`, na kterém běží Prometheus + Grafana.
- **`servers`** — pouze `localhost` s `ansible_connection: local`.

IP adresy si lze přizpůsobit své LXD síti

Pro nasazení na jinou infrastrukturu (např. vzdálený server) je nutné vytvořit analogický soubor
`inventory/remote` se stejnou strukturou, jen s jinými IP a případně SSH `ProxyJump` pro
skupinu `databases`. Mezi inventáři se přepíná parametrem `-i` u `ansible-playbook`, resp.
`-i <inventory>` u shell skriptů.

## Spuštění monitoringu

Nejdřív je potřeba spusit Grafana/Prometheus kontejner:

```bash
ansible-playbook setup/setup_monitoring.yml -i inventory/local
```

Po dokončení playbook vypíše URL a přihlašovací údaje (`admin`/`admin` dle
`roles/monitoring/defaults/main.yml`).

## Vytvoření databázových instancí

Jednotlivě (konkrétní databáze + HW profil):

```bash
ansible-playbook setup/setup.yml -i inventory/local -e "target=clickhousedb profile=medium"
```

Nebo hromadně přes wrapper skript:

```bash
./setup/setup_all.sh -p medium -i local
```

## Spouštění benchmarků

Hlavní CLI nástroj `tools/run_test.sh`:

```bash
./tools/run_test.sh -d clickhousedb -t insert -p medium -i local -r 3
```

| Přepínač                  | Popis                                                                               |
| ------------------------- | ----------------------------------------------------------------------------------- |
| `-d`, `-database`         | databáze k testování, nebo `*` pro všechny                                          |
| `-t`, `-test_type`        | `insert` \| `single_point` \| `condition` \| `aggregate` \| `live_insert`, nebo `*` |
| `-p`, `-profile`          | `small` \| `medium` \| `large` (viz `vars/resource_profiles.yml`)                   |
| `-r`, `-repeat`           | počet opakování celého běhu (default 1)                                             |
| `-i`, `-inventory`        | jméno inventory souboru (default `local`)                                           |
| `-rapid`                  | vynechá 3s odpočet před spuštěním                                                   |
| `-v`/`-vv`/`-vvv`/`-vvvv` | verbosity Ansible                                                                   |

Skript vždy zastaví ostatní databázové kontejnery, spustí cílovou databázi, provede test a
po skončení opět všechny kontejnery zastaví.

Pro test proudového zápisu (`live_insert`) slouží samostatný skript s dalšími parametry
(počet paralelních workerů, doba trvání, velikost batch, krok časové značky):

```bash
./tools/run_live_insert.sh -d '*' -limit postgres,mysql -p medium -w 4 -dur 120 -b 1000 -s 100
./tools/run_live_insert.sh --help   # kompletní přehled voleb
```

## Zastavení / smazání instancí

```bash
ansible-playbook setup/stop_vm.yml   -i inventory/local -e "target=clickhousedb"
ansible-playbook setup/delete_vm.yml -i inventory/local -e "target=clickhousedb"
```

či alternativně, pokud se nacházíme na hostu LXD

```bash
lxc stop clickhousedb
lxc delete clickhousedb
```

## HW profily a typy testů

`vars/resource_profiles.yml`:

| Profil | RAM  | CPU |
| ------ | ---- | --- |
| small  | 2GiB | 1   |
| medium | 4GiB | 2   |
| large  | 8GiB | 4   |

`vars/test_types.yml`: `insert`, `single_point`, `condition`, `aggregate`, `live_insert`.

## Výsledky

Každý testovací běh přidá jeden řádek (JSON) do
`results/<profil>-<test_type>.ndjson` — obsahuje databázi, dobu trvání dotazu, počet
přečtených/vrácených řádků, přidělený HW profil a u `live_insert` navíc počet workerů,
velikost batche a latence p50/p99. Zároveň se do Grafany zapíše anotace daného běhu.

## Poznámky

- Repozitář obsahuje i `Thesis/` s kompletní diplomovou prací — kapitola "Konfigurace
  testovacího prostředí a databázových systémů" popisuje architekturu i motivaci k
  jednotlivým rozhodnutím detailněji než tento README.
