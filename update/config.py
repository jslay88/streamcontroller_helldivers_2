"""
Configuration and constants for the Helldivers 2 StreamController plugin scripts.
"""

from pathlib import Path

# Base paths
SCRIPTS_DIR = Path(__file__).parent
PLUGIN_DIR = SCRIPTS_DIR.parent
ASSETS_DIR = PLUGIN_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
DATA_DIR = ASSETS_DIR / "data"
LOCALES_DIR = PLUGIN_DIR / "locales"

# Output files
STRATAGEMS_JSON = DATA_DIR / "stratagems.json"
MAPPINGS_JSON = DATA_DIR / "mappings.json"
LOCALE_EN_US = LOCALES_DIR / "en_US.json"

# GitHub repository URL for SVG icons
SVG_REPO_ZIP_URL = "https://github.com/nvigneux/Helldivers-2-Stratagems-icons-svg/archive/refs/heads/master.zip"
SVG_REPO_EXTRACTED_NAME = "Helldivers-2-Stratagems-icons-svg-master"

# Icon generation settings
DEFAULT_ICON_SIZE = 144
DEFAULT_ICON_SCALE = 0.70
DEFAULT_ICON_COLOR = "#c9b269"  # Gold fallback

# Color mappings: SVG colors -> desired PNG colors (more saturated)
COLOR_MAPPINGS = {
    "#c9b269": "#f0c628",  # Gold: muted -> saturated
    "#de7b6c": "#d11a38",  # Red/coral -> vivid red
    "#679552": "#60bf01",  # Green: muted -> vivid
}

# =============================================================================
# STRATAGEM MAPPINGS
# =============================================================================
# Unified mapping structure:
#   key: The internal plugin key (used in action IDs, icon filenames, locale keys)
#   wiki: The name as it appears on wiki.gg (for matching scraped data)
#   svg: The name as it appears in the SVG repository (for matching SVG files)
#   name: Human-readable display name (for locale generation)
#
# Add new stratagems here when they're discovered via the `discover` command.
# =============================================================================

STRATAGEM_MAPPINGS = {
    # =========================================================================
    # GENERAL STRATAGEMS
    # =========================================================================
    "Reinforce": {"wiki": "Reinforce", "svg": "Reinforce", "name": "Reinforce"},
    "Resupply": {"wiki": "Resupply", "svg": "Resupply", "name": "Resupply"},
    "SOSBeacon": {"wiki": "SoS Beacon", "svg": "SOS Beacon", "name": "SOS Beacon"},
    "UploadData": {"wiki": "Upload Data", "svg": "Upload Data", "name": "Upload Data"},
    "Hellbomb": {"wiki": "Hellbomb", "svg": "Hellbomb", "name": "Hellbomb"},
    "SEAFArtillery": {"wiki": "SEAF Artillery", "svg": "SEAF Artillery", "name": "SEAF Artillery"},
    "SuperEarthFlag": {"wiki": "Super Earth Flag", "svg": "Super Earth Flag", "name": "Super Earth Flag"},
    "SeismicProbe": {"wiki": "Seismic Probe", "svg": "Seismic Probe", "name": "Seismic Probe"},
    "ProspectingDrill": {"wiki": "Prospecting Drill", "svg": "Prospecting Drill", "name": "Prospecting Drill"},
    "IlluminationFlare": {"wiki": "Orbital Illumination Flare", "svg": "Orbital Illumination Flare", "name": "Illumination Flare"},
    "HiveBreakerDrill": {"wiki": "Hive Breaker Drill", "svg": "Hive Breaker Drill", "name": "Hive Breaker Drill"},
    "CargoContainer": {"wiki": "Cargo Container", "svg": "Cargo Container", "name": "Cargo Container"},
    "TectonicDrill": {"wiki": "Tectonic Drill", "svg": "Tectonic Drill", "name": "Tectonic Drill"},
    "DarkFluidVessel": {"wiki": "Dark Fluid Vessel", "svg": "Dark Fluid Vessel", "name": "Dark Fluid Vessel"},
    "SSDDelivery": {"wiki": "SSSD Delivery", "svg": "Upload Data", "name": "SSSD Delivery"},
    
    # =========================================================================
    # PATRIOTIC ADMINISTRATION CENTER (WEAPONS)
    # =========================================================================
    "MachineGun": {"wiki": "MG-43 Machine Gun", "svg": "Machine Gun", "name": "Machine Gun"},
    "AntiMaterialRifle": {"wiki": "APW-1 Anti-Materiel Rifle", "svg": "Anti-Materiel Rifle", "name": "Anti-Material Rifle"},
    "Stalwart": {"wiki": "M-105 Stalwart", "svg": "Stalwart", "name": "Stalwart"},
    "ExpendableAntiTank": {"wiki": "EAT-17 Expendable Anti-Tank", "svg": "Expendable Anti-Tank", "name": "Expendable Anti-Tank"},
    "RecoillessRifle": {"wiki": "GR-8 Recoilless Rifle", "svg": "Recoilless Rifle", "name": "Recoilless Rifle"},
    "Flamethrower": {"wiki": "FLAM-40 Flamethrower", "svg": "Flamethrower", "name": "Flamethrower"},
    "Autocannon": {"wiki": "AC-8 Autocannon", "svg": "Autocannon", "name": "Autocannon"},
    "HeavyMachineGun": {"wiki": "MG-206 Heavy Machine Gun", "svg": "Heavy Machine Gun", "name": "Heavy Machine Gun"},
    "AirburstRocketLauncher": {"wiki": "RL-77 Airburst Rocket Launcher", "svg": "Airburst Rocket Launcher", "name": "Airburst Rocket Launcher"},
    "Commando": {"wiki": "MLS-4X Commando", "svg": "Commando", "name": "Commando"},
    "Railgun": {"wiki": "RS-422 Railgun", "svg": "Railgun", "name": "Railgun"},
    "SPEARLauncher": {"wiki": "FAF-14 Spear", "svg": "Spear", "name": "SPEAR Launcher"},
    "WASPLauncher": {"wiki": "StA-X3 W.A.S.P. Launcher", "svg": "StA-X3 W.A.S.P. Launcher", "name": "W.A.S.P. Launcher"},
    
    # =========================================================================
    # ORBITAL CANNONS
    # =========================================================================
    "OrbitalGatlingBarrage": {"wiki": "Orbital Gatling Barrage", "svg": "Orbital Gatling Barrage", "name": "Orbital Gatling Barrage"},
    "OrbitalAirburstStrike": {"wiki": "Orbital Airburst Strike", "svg": "Orbital Airburst Strike", "name": "Orbital Airburst Strike"},
    "Orbital120MMHEBarrage": {"wiki": "Orbital 120mm HE Barrage", "svg": "Orbital 120MM HE Barrage", "name": "Orbital 120MM HE Barrage"},
    "Orbital380MMHEBarrage": {"wiki": "Orbital 380mm HE Barrage", "svg": "Orbital 380MM HE Barrage", "name": "Orbital 380MM HE Barrage"},
    "OrbitalWalkingBarrage": {"wiki": "Orbital Walking Barrage", "svg": "Orbital Walking Barrage", "name": "Orbital Walking Barrage"},
    "OrbitalLaser": {"wiki": "Orbital Laser", "svg": "Orbital Laser", "name": "Orbital Laser"},
    "OrbitalNapalmBarrage": {"wiki": "Orbital Napalm Barrage", "svg": "Orbital Napalm Barrage", "name": "Orbital Napalm Barrage"},
    "OrbitalRailcannonStrike": {"wiki": "Orbital Railcannon Strike", "svg": "Orbital Railcannon Strike", "name": "Orbital Railcannon Strike"},
    
    # =========================================================================
    # BRIDGE
    # =========================================================================
    "OrbitalPrecisionStrike": {"wiki": "Orbital Precision Strike", "svg": "Orbital Precision Strike", "name": "Orbital Precision Strike"},
    "OrbitalGasStrike": {"wiki": "Orbital Gas Strike", "svg": "Orbital Gas Strike", "name": "Orbital Gas Strike"},
    "OrbitalEMSStrike": {"wiki": "Orbital EMS Strike", "svg": "Orbital EMS Strike", "name": "Orbital EMS Strike"},
    "OrbitalSmokeStrike": {"wiki": "Orbital Smoke Strike", "svg": "Orbital Smoke Strike", "name": "Orbital Smoke Strike"},
    "HMGEmplacement": {"wiki": "E/MG-101 HMG Emplacement", "svg": "HMG Emplacement", "name": "HMG Emplacement"},
    "ShieldGenerator": {"wiki": "FX-12 Shield Generator Relay", "svg": "Shield Generator Relay", "name": "Shield Generator Relay"},
    "TeslaTower": {"wiki": "A/ARC-3 Tesla Tower", "svg": "Tesla Tower", "name": "Tesla Tower"},
    "GrenadierBattlement": {"wiki": "E/GL-21 Grenadier Battlement", "svg": "Grenadier Battlement", "name": "Grenadier Battlement"},
    
    # =========================================================================
    # HANGAR
    # =========================================================================
    "EagleStrafingRun": {"wiki": "Eagle Strafing Run", "svg": "Eagle Strafing Run", "name": "Eagle Strafing Run"},
    "EagleAirstrike": {"wiki": "Eagle Airstrike", "svg": "Eagle Airstrike", "name": "Eagle Airstrike"},
    "EagleClusterBomb": {"wiki": "Eagle Cluster Bomb", "svg": "Eagle Cluster Bomb", "name": "Eagle Cluster Bomb"},
    "EagleNapalmAirstrike": {"wiki": "Eagle Napalm Airstrike", "svg": "Eagle Napalm Airstrike", "name": "Eagle Napalm Airstrike"},
    "JumpPack": {"wiki": "LIFT-850 Jump Pack", "svg": "Jump Pack", "name": "Jump Pack"},
    "EagleSmokeStrike": {"wiki": "Eagle Smoke Strike", "svg": "Eagle Smoke Strike", "name": "Eagle Smoke Strike"},
    "Eagle110MMRocketPods": {"wiki": "Eagle 110mm Rocket Pods", "svg": "Eagle 110MM Rocket Pods", "name": "Eagle 110MM Rocket Pods"},
    "Eagle500kgBomb": {"wiki": "Eagle 500kg Bomb", "svg": "Eagle 500KG Bomb", "name": "Eagle 500kg Bomb"},
    "FastReconVehicle": {"wiki": "M-102 Fast Recon Vehicle", "svg": "Fast Recon Vehicle", "name": "Fast Recon Vehicle"},
    "EagleRearm": {"wiki": "Eagle Rearm", "svg": "Eagle Rearm", "name": "Eagle Rearm"},
    
    # =========================================================================
    # ENGINEERING BAY
    # =========================================================================
    "AntiPersonnelMinefield": {"wiki": "MD-6 Anti-Personnel Minefield", "svg": "Anti-Personnel Minefield", "name": "Anti-Personnel Minefield"},
    "SupplyPack": {"wiki": "B-1 Supply Pack", "svg": "Supply Pack", "name": "Supply Pack"},
    "GrenadeLauncher": {"wiki": "GL-21 Grenade Launcher", "svg": "Grenade Launcher", "name": "Grenade Launcher"},
    "LaserCannon": {"wiki": "LAS-98 Laser Cannon", "svg": "Laser Cannon", "name": "Laser Cannon"},
    "IncendiaryMines": {"wiki": "MD-I4 Incendiary Mines", "svg": "Incendiary Mines", "name": "Incendiary Mines"},
    "GuardDogRover": {"wiki": "AX/LAS-5 \"Guard Dog\" Rover", "svg": "Guard Dog Rover", "name": "\"Guard Dog\" Rover"},
    "BallisticShield": {"wiki": "SH-20 Ballistic Shield Backpack", "svg": "Ballistic Shield Backpack", "name": "Ballistic Shield"},
    "ArcThrower": {"wiki": "ARC-3 Arc Thrower", "svg": "Arc Thrower", "name": "Arc Thrower"},
    "QuasarCannon": {"wiki": "LAS-99 Quasar Cannon", "svg": "Quasar Cannon", "name": "Quasar Cannon"},
    "ShieldPack": {"wiki": "SH-32 Shield Generator Pack", "svg": "Shield Generator Pack", "name": "Shield Generator Pack"},
    "AntiTankMines": {"wiki": "MD-17 Anti-Tank Mines", "svg": "Anti-Tank Mines", "name": "Anti-Tank Mines"},
    "GasMine": {"wiki": "MD-8 Gas Mines", "svg": "Gas Mine", "name": "Gas Mine"},
    
    # =========================================================================
    # ROBOTICS WORKSHOP
    # =========================================================================
    "MachineGunSentry": {"wiki": "A/MG-43 Machine Gun Sentry", "svg": "Machine Gun Sentry", "name": "Machine Gun Sentry"},
    "GatlingSentry": {"wiki": "A/G-16 Gatling Sentry", "svg": "Gatling Sentry", "name": "Gatling Sentry"},
    "MortarSentry": {"wiki": "A/M-12 Mortar Sentry", "svg": "Mortar Sentry", "name": "Mortar Sentry"},
    "GuardDog": {"wiki": "AX/AR-23 \"Guard Dog\"", "svg": "Guard Dog", "name": "Guard Dog"},
    "AutocannonSentry": {"wiki": "A/AC-8 Autocannon Sentry", "svg": "Autocannon Sentry", "name": "Autocannon Sentry"},
    "RocketSentry": {"wiki": "A/MLS-4X Rocket Sentry", "svg": "Rocket Sentry", "name": "Rocket Sentry"},
    "EMSMortarSentry": {"wiki": "A/M-23 EMS Mortar Sentry", "svg": "EMS Mortar Sentry", "name": "EMS Mortar Sentry"},
    "PatriotExosuit": {"wiki": "EXO-45 Patriot Exosuit", "svg": "Patriot Exosuit", "name": "Patriot Exosuit"},
    "EmancipatorExosuit": {"wiki": "EXO-49 Emancipator Exosuit", "svg": "Emancipator Exosuit", "name": "Emancipator Exosuit"},
    
    # =========================================================================
    # CHEMICAL AGENTS
    # =========================================================================
    "Sterilizer": {"wiki": "TX-41 Sterilizer", "svg": "Sterilizer", "name": "Sterilizer"},
    "GuardDogBreath": {"wiki": "AX/TX-13 \"Guard Dog\" Dog Breath", "svg": "Guard Dog Breath", "name": "\"Guard Dog\" Dog Breath"},
    
    # =========================================================================
    # URBAN LEGENDS
    # =========================================================================
    "DirectionalShield": {"wiki": "SH-51 Directional Shield", "svg": "Directional Shield", "name": "Directional Shield"},
    "FlameSentry": {"wiki": "A/FLAM-40 Flame Sentry", "svg": "Flame Sentry", "name": "Flame Sentry"},
    "AntiTankEmplacement": {"wiki": "E/AT-12 Anti-Tank Emplacement", "svg": "Anti-Tank Emplacement", "name": "Anti-Tank Emplacement"},
    
    # =========================================================================
    # SERVANTS OF FREEDOM
    # =========================================================================
    "HellbombPortable": {"wiki": "B-100 Portable Hellbomb", "svg": "Hellbomb Portable", "name": "Portable Hellbomb"},
    
    # =========================================================================
    # BORDERLINE JUSTICE
    # =========================================================================
    "HoverPack": {"wiki": "LIFT-860 Hover Pack", "svg": "Hover Pack", "name": "Hover Pack"},
    
    # =========================================================================
    # MASTERS OF CEREMONY
    # =========================================================================
    "OneTrueFlag": {"wiki": "CQC-1 One True Flag", "svg": "One True Flag", "name": "One True Flag"},
    
    # =========================================================================
    # FORCE OF LAW
    # =========================================================================
    "GL52DeEscalator": {"wiki": "GL-52 De-Escalator", "svg": "GL-52 De-Escalator", "name": "GL-52 De-Escalator"},
    "GuardDogK9": {"wiki": "AX/ARC-3 \"Guard Dog\" K-9", "svg": "Guard Dog K-9", "name": "\"Guard Dog\" K-9"},
    
    # =========================================================================
    # CONTROL GROUP
    # =========================================================================
    "LaserSentry": {"wiki": "A/LAS-98 Laser Sentry", "svg": "Laser Sentry", "name": "Laser Sentry"},
    "WarpPack": {"wiki": "LIFT-182 Warp Pack", "svg": "Warp Pack", "name": "Warp Pack"},
    "Epoch": {"wiki": "PLAS-45 Epoch", "svg": "Epoch", "name": "Epoch"},
    
    # =========================================================================
    # DUST DEVILS
    # =========================================================================
    "SoloSilo": {"wiki": "MS-11 Solo Silo", "svg": "Solo Silo", "name": "Solo Silo"},
    "ExpendableNapalm": {"wiki": "EAT-700 Expendable Napalm", "svg": "Expendable Napalm", "name": "Expendable Napalm"},
    "Speargun": {"wiki": "S-11 Speargun", "svg": "Speargun", "name": "Speargun"},
    
    # =========================================================================
    # PYTHON COMMANDOS
    # =========================================================================
    "Maxigun": {"wiki": "M-1000 Maxigun", "svg": "Maxigun", "name": "Maxigun"},
    "DefoliationTool": {"wiki": "CQC-9 Defoliation Tool", "svg": "Defoliation Tool", "name": "Defoliation Tool"},
    "GuardDogHotDog": {"wiki": "AX/FLAM-75 \"Guard Dog\" Hot Dog", "svg": "Guard Dog Hot Dog", "name": "\"Guard Dog\" Hot Dog"},
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_all_keys() -> list[str]:
    """Get list of all stratagem keys."""
    return list(STRATAGEM_MAPPINGS.keys())


def get_wiki_to_key_mapping() -> dict[str, str]:
    """Get mapping from wiki names to internal keys."""
    return {
        data["wiki"]: key
        for key, data in STRATAGEM_MAPPINGS.items()
        if data.get("wiki")
    }


def get_svg_to_key_mapping() -> dict[str, str]:
    """Get mapping from SVG names to internal keys."""
    return {
        data["svg"]: key
        for key, data in STRATAGEM_MAPPINGS.items()
        if data.get("svg")
    }


def get_key_to_svg_mapping() -> dict[str, str]:
    """Get mapping from internal keys to SVG names."""
    return {
        key: data["svg"]
        for key, data in STRATAGEM_MAPPINGS.items()
        if data.get("svg")
    }


def get_display_names() -> dict[str, str]:
    """Get mapping from internal keys to display names."""
    return {
        key: data.get("name", key)
        for key, data in STRATAGEM_MAPPINGS.items()
    }


def get_stratagem_info(key: str) -> dict | None:
    """Get full info for a stratagem by its internal key."""
    return STRATAGEM_MAPPINGS.get(key)


# Derived mappings for convenience
SVG_TO_KEY_MAPPINGS = get_svg_to_key_mapping()
KEY_TO_SVG_MAPPINGS = get_key_to_svg_mapping()
DISPLAY_NAMES = get_display_names()
WIKI_TO_KEY_MAPPINGS = get_wiki_to_key_mapping()

# Legacy compatibility
LEGACY_KEYS = get_all_keys()
