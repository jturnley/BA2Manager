# Manage BA2 PRO - Fallout 4 BA2 Extraction Tool (Mod Organizer 2)
# Purpose: Extract BA2 files to stay within Fallout 4's ~255 BA2 limit
# Requires: Mod Organizer 2, PowerShell 5.1+
# Author: Illrigger
# Date: November 19, 2025
# Version: PRO (No informational text - menus only)
# Note: Core logic is kept in sync with manage_ba2.ps1; this version just omits
#       the in-script explanations and helper text.

# WHY EXTRACT? Extracting BA2s reduces file count without breaking mod dependencies.
# Merging BA2s can cause issues with mod load order and plugin dependencies.

#Requires -Version 5.1

# ============================================
# Configuration
# ============================================
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Archive2Path = Join-Path $ScriptDir "Archive2.exe"
$MO2ModsDir = "mods"
$BackupDir = Join-Path $ScriptDir "mod_backups"
$LogFile = "BA2_Extract.log"
$FailedExtractionsFile = "failed_extractions.txt"

# ============================================
# Creation Club Name Mapping
# ============================================
$CCNames = @{
    "ccacxfo4001" = @{Name = "Vault Suit Customization"; BA2Count = 2}
    "ccawnfo4001" = @{Name = "Graphic T-Shirt Pack"; BA2Count = 2}
    "ccawnfo4002" = @{Name = "Faction Clothing Pack"; BA2Count = 2}
    "ccbgsfo4001" = @{Name = "Pip-Boy Paint - Black"; BA2Count = 2}
    "ccbgsfo4002" = @{Name = "Pip-Boy Paint - Blue"; BA2Count = 2}
    "ccbgsfo4003" = @{Name = "Pip-Boy Paint - Desert Camo"; BA2Count = 2}
    "ccbgsfo4004" = @{Name = "Pip-Boy Paint - Swamp Camo"; BA2Count = 2}
    "ccbgsfo4005" = @{Name = "Pip-Boy Paint - Aquatic Camo"; BA2Count = 2}
    "ccbgsfo4006" = @{Name = "Pip-Boy Paint - Chrome"; BA2Count = 2}
    "ccbgsfo4008" = @{Name = "Pip-Boy Paint - Green"; BA2Count = 2}
    "ccbgsfo4009" = @{Name = "Pip-Boy Paint - Orange"; BA2Count = 2}
    "ccbgsfo4010" = @{Name = "Pip-Boy Paint - Pink"; BA2Count = 2}
    "ccbgsfo4011" = @{Name = "Pip-Boy Paint - Purple"; BA2Count = 2}
    "ccbgsfo4012" = @{Name = "Pip-Boy Paint - Red"; BA2Count = 2}
    "ccbgsfo4013" = @{Name = "Pip-Boy Paint - Tan"; BA2Count = 2}
    "ccbgsfo4014" = @{Name = "Pip-Boy Paint - Silver White"; BA2Count = 2}
    "ccbgsfo4015" = @{Name = "Pip-Boy Paint - Yellow"; BA2Count = 2}
    "ccbgsfo4016" = @{Name = "Pip-Boy Paint - Prey (Corvega)"; BA2Count = 2}
    "ccbgsfo4018" = @{Name = "Prototype Gauss Rifle"; BA2Count = 2}
    "ccbgsfo4019" = @{Name = "Chinese Stealth Armor"; BA2Count = 2}
    "ccbgsfo4020" = @{Name = "Power Armor Paint - Onyx"; BA2Count = 2}
    "ccbgsfo4021" = @{Name = "Power Armor Paint - Blue"; BA2Count = 2}
    "ccbgsfo4022" = @{Name = "Power Armor Paint - Desert Camo"; BA2Count = 2}
    "ccbgsfo4023" = @{Name = "Power Armor Paint - Swamp Camo"; BA2Count = 2}
    "ccbgsfo4024" = @{Name = "Power Armor Paint - Aquatic Camo"; BA2Count = 2}
    "ccbgsfo4025" = @{Name = "Power Armor Paint - Chrome"; BA2Count = 2}
    "ccbgsfo4027" = @{Name = "Power Armor Paint - Green"; BA2Count = 2}
    "ccbgsfo4028" = @{Name = "Power Armor Paint - Orange"; BA2Count = 2}
    "ccbgsfo4029" = @{Name = "Power Armor Paint - Pink"; BA2Count = 2}
    "ccbgsfo4030" = @{Name = "Power Armor Paint - Purple"; BA2Count = 2}
    "ccbgsfo4031" = @{Name = "Power Armor Paint - Red"; BA2Count = 2}
    "ccbgsfo4032" = @{Name = "Power Armor Paint - Tan"; BA2Count = 2}
    "ccbgsfo4033" = @{Name = "Power Armor Paint - White"; BA2Count = 2}
    "ccbgsfo4034" = @{Name = "Power Armor Paint - Yellow"; BA2Count = 2}
    "ccbgsfo4035" = @{Name = "Pint-Sized Slasher"; BA2Count = 2}
    "ccbgsfo4036" = @{Name = "TransDOGrifier"; BA2Count = 2}
    "ccbgsfo4038" = @{Name = "Horse Power Armor"; BA2Count = 2}
    "ccbgsfo4041" = @{Name = "Doom Classic Marine Armor"; BA2Count = 2}
    "ccbgsfo4042" = @{Name = "Doom BFG"; BA2Count = 2}
    "ccbgsfo4044" = @{Name = "Hellfire Power Armor"; BA2Count = 2}
    "ccbgsfo4045" = @{Name = "Arcade Workshop Pack"; BA2Count = 2}
    "ccbgsfo4046" = @{Name = "Tesla Cannon"; BA2Count = 2}
    "ccbgsfo4047" = @{Name = "Quake Thunderbolt"; BA2Count = 2}
    "ccbgsfo4048" = @{Name = "Fantasy Hero Set"; BA2Count = 2}
    "ccbgsfo4049" = @{Name = "Brahmin Armor"; BA2Count = 2}
    "ccbgsfo4050" = @{Name = "Dog Skin - Border Collie"; BA2Count = 2}
    "ccbgsfo4051" = @{Name = "Dog Skin - Boxer"; BA2Count = 2}
    "ccbgsfo4052" = @{Name = "Dog Skin - Dalmatian"; BA2Count = 2}
    "ccbgsfo4053" = @{Name = "Dog Skin - Golden Retriever"; BA2Count = 2}
    "ccbgsfo4054" = @{Name = "Dog Skin - Great Dane"; BA2Count = 2}
    "ccbgsfo4055" = @{Name = "Dog Skin - Husky"; BA2Count = 2}
    "ccbgsfo4056" = @{Name = "Dog Skin - Black Labrador"; BA2Count = 2}
    "ccbgsfo4057" = @{Name = "Dog Skin - Yellow Labrador"; BA2Count = 2}
    "ccbgsfo4058" = @{Name = "Dog Skin - Chocolate Labrador"; BA2Count = 2}
    "ccbgsfo4059" = @{Name = "Dog Skin - Pitbull"; BA2Count = 2}
    "ccbgsfo4060" = @{Name = "Dog Skin - Rottweiler"; BA2Count = 2}
    "ccbgsfo4061" = @{Name = "Dog Skin - Shiba Inu"; BA2Count = 2}
    "ccbgsfo4062" = @{Name = "Pip-Boy Paint - Patriotic"; BA2Count = 2}
    "ccbgsfo4063" = @{Name = "Power Armor Paint - Patriotic"; BA2Count = 2}
    "ccbgsfo4070" = @{Name = "Pip-Boy Paint - Abraxo"; BA2Count = 2}
    "ccbgsfo4071" = @{Name = "Pip-Boy Paint - ArcJet"; BA2Count = 2}
    "ccbgsfo4072" = @{Name = "Pip-Boy Paint - Grognak"; BA2Count = 2}
    "ccbgsfo4073" = @{Name = "Pip-Boy Paint - Manta Man"; BA2Count = 2}
    "ccbgsfo4074" = @{Name = "Pip-Boy Paint - The Inspector"; BA2Count = 2}
    "ccbgsfo4075" = @{Name = "Pip-Boy Paint - Silver Shroud"; BA2Count = 2}
    "ccbgsfo4076" = @{Name = "Pip-Boy Paint - Mistress of Mystery"; BA2Count = 2}
    "ccbgsfo4077" = @{Name = "Pip-Boy Paint - Red Rocket"; BA2Count = 2}
    "ccbgsfo4078" = @{Name = "Pip-Boy Paint - Reilly's Rangers"; BA2Count = 2}
    "ccbgsfo4079" = @{Name = "Pip-Boy Paint - Vim!"; BA2Count = 2}
    "ccbgsfo4080" = @{Name = "Pip-Boy Paint - Pop"; BA2Count = 2}
    "ccbgsfo4081" = @{Name = "Pip-Boy Paint - Phenol Resin"; BA2Count = 2}
    "ccbgsfo4082" = @{Name = "Pip-Boy Paint - Five-Star Red"; BA2Count = 2}
    "ccbgsfo4083" = @{Name = "Pip-Boy Paint - Art Deco"; BA2Count = 2}
    "ccbgsfo4084" = @{Name = "Pip-Boy Paint - Adventure"; BA2Count = 2}
    "ccbgsfo4085" = @{Name = "Pip-Boy Paint - Hawaii"; BA2Count = 2}
    "ccbgsfo4086" = @{Name = "Pip-Boy Paint - Corvega"; BA2Count = 2}
    "ccbgsfo4087" = @{Name = "Pip-Boy Paint - Haida"; BA2Count = 2}
    "ccbgsfo4089" = @{Name = "Pip-Boy Paint - Neon Sunrise"; BA2Count = 2}
    "ccbgsfo4090" = @{Name = "Pip-Boy Paint - Tribal"; BA2Count = 2}
    "ccbgsfo4091" = @{Name = "Armor Skin - Bats"; BA2Count = 2}
    "ccbgsfo4092" = @{Name = "Armor Skin - Aquatic Camo"; BA2Count = 2}
    "ccbgsfo4093" = @{Name = "Armor Skin - Swamp Camo"; BA2Count = 2}
    "ccbgsfo4094" = @{Name = "Armor Skin - Desert Camo"; BA2Count = 2}
    "ccbgsfo4095" = @{Name = "Armor Skin - Children of Atom"; BA2Count = 2}
    "ccbgsfo4096" = @{Name = "Armor Skin - Enclave"; BA2Count = 2}
    "ccbgsfo4097" = @{Name = "Armor Skin - Jack O'Lantern"; BA2Count = 2}
    "ccbgsfo4098" = @{Name = "Armor Skin - Pickman"; BA2Count = 2}
    "ccbgsfo4099" = @{Name = "Armor Skin - Reilly's Rangers"; BA2Count = 2}
    "ccbgsfo4101" = @{Name = "Armor Skin - Shi"; BA2Count = 2}
    "ccbgsfo4103" = @{Name = "Armor Skin - Tunnel Snakes"; BA2Count = 2}
    "ccbgsfo4104" = @{Name = "Weapon Skin - Bats"; BA2Count = 2}
    "ccbgsfo4105" = @{Name = "Weapon Skin - Aquatic Camo"; BA2Count = 2}
    "ccbgsfo4106" = @{Name = "Weapon Skin - Swamp Camo"; BA2Count = 2}
    "ccbgsfo4107" = @{Name = "Weapon Skin - Desert Camo"; BA2Count = 2}
    "ccbgsfo4108" = @{Name = "Weapon Skin - Children of Atom"; BA2Count = 2}
    "ccbgsfo4110" = @{Name = "Weapon Skin - Enclave"; BA2Count = 2}
    "ccbgsfo4111" = @{Name = "Weapon Skin - Jack O'Lantern"; BA2Count = 2}
    "ccbgsfo4112" = @{Name = "Weapon Skin - Pickman"; BA2Count = 2}
    "ccbgsfo4113" = @{Name = "Weapon Skin - Reilly's Rangers"; BA2Count = 2}
    "ccbgsfo4114" = @{Name = "Weapon Skin - Shi"; BA2Count = 2}
    "ccbgsfo4115" = @{Name = "X-02 Power Armor"; BA2Count = 2}
    "ccbgsfo4116" = @{Name = "Heavy Incinerator"; BA2Count = 2}
    "ccbgsfo4117" = @{Name = "Capital Wasteland Mercenaries"; BA2Count = 2}
    "ccbgsfo4118" = @{Name = "Weapon Skin - Tunnel Snakes"; BA2Count = 2}
    "ccbgsfo4119" = @{Name = "Cyber Dog"; BA2Count = 2}
    "ccbgsfo4120" = @{Name = "Power Armor Paint - Pitt Raider"; BA2Count = 2}
    "ccbgsfo4121" = @{Name = "Power Armor Paint - Air Force"; BA2Count = 2}
    "ccbgsfo4122" = @{Name = "Power Armor Paint - Scorched Sierra"; BA2Count = 2}
    "ccbgsfo4123" = @{Name = "Power Armor Paint - Inferno"; BA2Count = 2}
    "ccbgsfo4124" = @{Name = "Repurposed Power Armor Helmets"; BA2Count = 2}
    "cccrsfo4001" = @{Name = "Pip-Boy Paint - Children of Atom"; BA2Count = 2}
    "cceejfo4001" = @{Name = "Home Decor Workshop Pack"; BA2Count = 2}
    "cceejfo4002" = @{Name = "Nuka-Cola Collector Workshop"; BA2Count = 2}
    "ccfrsfo4001" = @{Name = "Handmade Shotgun"; BA2Count = 2}
    "ccfrsfo4002" = @{Name = "Anti-Materiel Rifle"; BA2Count = 2}
    "ccfrsfo4003" = @{Name = "CR-74L Combat Rifle"; BA2Count = 2}
    "ccfsvfo4001" = @{Name = "Modular Military Backpack"; BA2Count = 2}
    "ccfsvfo4002" = @{Name = "Modern Furniture Workshop Pack"; BA2Count = 2}
    "ccfsvfo4003" = @{Name = "Coffee and Donuts Workshop Pack"; BA2Count = 2}
    "ccfsvfo4007" = @{Name = "Halloween Workshop Pack"; BA2Count = 2}
    "ccgcafo4001" = @{Name = "Weapon Skin - Army"; BA2Count = 2}
    "ccgcafo4002" = @{Name = "Weapon Skin - Atom Cats"; BA2Count = 2}
    "ccgcafo4003" = @{Name = "Weapon Skin - Brotherhood of Steel"; BA2Count = 2}
    "ccgcafo4004" = @{Name = "Weapon Skin - Gunners"; BA2Count = 2}
    "ccgcafo4005" = @{Name = "Weapon Skin - Hot Rod Pink Flames"; BA2Count = 2}
    "ccgcafo4006" = @{Name = "Weapon Skin - Hot Rod Shark"; BA2Count = 2}
    "ccgcafo4007" = @{Name = "Weapon Skin - Hot Rod Red Flames"; BA2Count = 2}
    "ccgcafo4008" = @{Name = "Weapon Skin - The Institute"; BA2Count = 2}
    "ccgcafo4009" = @{Name = "Weapon Skin - Minutemen"; BA2Count = 2}
    "ccgcafo4010" = @{Name = "Weapon Skin - Railroad"; BA2Count = 2}
    "ccgcafo4011" = @{Name = "Weapon Skin - Vault-Tec"; BA2Count = 2}
    "ccgcafo4012" = @{Name = "Armor Skin - Atom Cats"; BA2Count = 2}
    "ccgcafo4013" = @{Name = "Armor Skin - Brotherhood of Steel"; BA2Count = 2}
    "ccgcafo4014" = @{Name = "Armor Skin - Gunners"; BA2Count = 2}
    "ccgcafo4015" = @{Name = "Armor Skin - Hot Rod Pink Flames"; BA2Count = 2}
    "ccgcafo4016" = @{Name = "Armor Skin - Hot Rod Shark"; BA2Count = 2}
    "ccgcafo4017" = @{Name = "Armor Skin - The Institute"; BA2Count = 2}
    "ccgcafo4018" = @{Name = "Armor Skin - Minutemen"; BA2Count = 2}
    "ccgcafo4019" = @{Name = "Armor Skin - Nuka Cherry"; BA2Count = 2}
    "ccgcafo4020" = @{Name = "Armor Skin - Railroad"; BA2Count = 2}
    "ccgcafo4021" = @{Name = "Armor Skin - Hot Rod Red Flames"; BA2Count = 2}
    "ccgcafo4022" = @{Name = "Armor Skin - Vault-Tec"; BA2Count = 2}
    "ccgcafo4023" = @{Name = "Armor Skin - Army"; BA2Count = 2}
    "ccgcafo4024" = @{Name = "Institute Plasma Weapons"; BA2Count = 2}
    "ccgcafo4025" = @{Name = "Power Armor Paint - Gunners vs. Minutemen"; BA2Count = 2}
    "ccgrcfo4001" = @{Name = "Pip-Boy Paint - Grey Tortoise"; BA2Count = 2}
    "ccgrcfo4002" = @{Name = "Pip-Boy Paint - Green Vim"; BA2Count = 2}
    "ccjvdfo4001" = @{Name = "Holiday Workshop Pack"; BA2Count = 2}
    "cckgjfo4001" = @{Name = "Settlement Ambush Kit"; BA2Count = 2}
    "ccotmfo4001" = @{Name = "Enclave Remnants"; BA2Count = 2}
    "ccqdrfo4001" = @{Name = "Sentinel Control System Companion"; BA2Count = 2}
    "ccrpsfo4001" = @{Name = "Sea Scavengers"; BA2Count = 2}
    "ccrzrfo4001" = @{Name = "Tunnel Snakes Rule!"; BA2Count = 2}
    "ccrzrfo4002" = @{Name = "Zetan Arsenal"; BA2Count = 2}
    "ccrzrfo4003" = @{Name = "Pip-Boy Paint - Overseer's Edition"; BA2Count = 2}
    "ccrzrfo4004" = @{Name = "Pip-Boy Paint - Institute"; BA2Count = 2}
    "ccsbjfo4001" = @{Name = "Solar Cannon"; BA2Count = 2}
    "ccsbjfo4002" = @{Name = "Manwell Rifle Set"; BA2Count = 2}
    "ccsbjfo4003" = @{Name = "Makeshift Weapon Pack"; BA2Count = 2}
    "ccsbjfo4004" = @{Name = "Ion Gun"; BA2Count = 2}
    "ccswkfo4001" = @{Name = "Captain Cosmos"; BA2Count = 2}
    "ccswkfo4002" = @{Name = "Pip-Boy Paint - Nuka-Cola"; BA2Count = 2}
    "ccswkfo4003" = @{Name = "Pip-Boy Paint - Nuka-Cola Quantum"; BA2Count = 2}
    "cctosfo4001" = @{Name = "Virtual Workshop: Grid World"; BA2Count = 2}
    "cctosfo4002" = @{Name = "Neon Flats"; BA2Count = 2}
    "ccvltfo4001" = @{Name = "Noir Penthouse"; BA2Count = 2}
    "ccygpfo4001" = @{Name = "Pip-Boy Paint - Cruiser"; BA2Count = 2}
    "cczsef04001" = @{Name = "Charlestown Condo"; BA2Count = 2}
    "cczsefo4002" = @{Name = "Shroud Manor"; BA2Count = 2}

}

# ============================================
# Helper Functions
# ============================================
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$timestamp] $Message" | Out-File -FilePath $LogFile -Append
}

function Show-Header {
    Clear-Host
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Manage BA2 - Fallout 4 BA2 Extractor" -ForegroundColor Cyan
    Write-Host "  (Mod Organizer 2 - Anniversary Edition Fix)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "MO2 Directory: $PWD" -ForegroundColor Gray
    
    # Show active paths for clarity
    $fo4PathHeader = $null
    try {
        $mo2IniPath = "ModOrganizer.ini"
        if (Test-Path $mo2IniPath) {
            $iniContent = Get-Content $mo2IniPath -ErrorAction Stop
            $gamePathLine = $iniContent | Where-Object { $_ -match '^gamePath=' }
            if ($gamePathLine) {
                if ($gamePathLine -match '@ByteArray\((.+)\)') {
                    $fo4PathHeader = $matches[1] -replace '\\\\', '\\'
                } else {
                    $fo4PathHeader = ($gamePathLine -replace '^gamePath=', '').Trim()
                }
            }
        }
    } catch { }
    $fo4Disp = if ($fo4PathHeader) { $fo4PathHeader } else { "N/A" }
    $cccDisp = if ($fo4PathHeader) { (Join-Path $fo4PathHeader "Fallout4.ccc") } else { "N/A" }
    $modsDisp = try { if (Test-Path $MO2ModsDir) { (Resolve-Path $MO2ModsDir).Path } else { (Join-Path $PWD $MO2ModsDir) } } catch { (Join-Path $PWD $MO2ModsDir) }
    $a2Disp = if (Test-Path $Archive2Path) { $Archive2Path } else { "$Archive2Path (missing)" }
    Write-Host "Active Paths: FO4=$fo4Disp | CCC=$cccDisp | Mods=$modsDisp | A2=$a2Disp" -ForegroundColor DarkGray
    Write-Host ""
}

function Show-BA2Count {
    param([int]$Count)
    
    $countColor = "Green"
    if ($Count -gt 500) {
        $countColor = "Red"
    } elseif ($Count -gt 350) {
        $countColor = "Yellow"
    }
    
    Write-Host "Current BA2 Count: " -ForegroundColor Cyan -NoNewline
    Write-Host "$Count" -ForegroundColor $countColor
    Write-Host "Required: " -NoNewline
    Write-Host "Under 500" -ForegroundColor Yellow -NoNewline
    Write-Host "  |  Ideal: " -NoNewline
    Write-Host "Under 350" -ForegroundColor Green
    Write-Host ""
}

function Get-PluginMasters {
    param([string]$PluginPath)
    
    if (-not (Test-Path $PluginPath)) {
        return @()
    }
    
    try {
        $stream = [System.IO.File]::OpenRead($PluginPath)
        $reader = New-Object System.IO.BinaryReader($stream)
        
        # Read TES4 header
        $type = [System.Text.Encoding]::ASCII.GetString($reader.ReadBytes(4))
        if ($type -ne "TES4") {
            $reader.Close()
            $stream.Close()
            return @()
        }
        
        # Skip header size and flags
        $reader.ReadUInt32() | Out-Null
        $reader.ReadUInt32() | Out-Null
        $reader.ReadUInt32() | Out-Null
        $reader.ReadUInt16() | Out-Null
        $reader.ReadUInt16() | Out-Null
        
        $masters = @()
        
        # Read subrecords until we hit end of header or find all masters
        while ($stream.Position -lt $stream.Length) {
            $subType = [System.Text.Encoding]::ASCII.GetString($reader.ReadBytes(4))
            $subSize = $reader.ReadUInt16()
            
            if ($subType -eq "MAST") {
                # Read master filename (null-terminated string)
                $masterBytes = $reader.ReadBytes($subSize)
                $masterName = [System.Text.Encoding]::ASCII.GetString($masterBytes).TrimEnd([char]0)
                $masters += $masterName.ToLower()
            } elseif ($subType -eq "HEDR") {
                # We've passed the masters section, break
                break
            } else {
                # Skip this subrecord
                $reader.ReadBytes($subSize) | Out-Null
            }
        }
        
        $reader.Close()
        $stream.Close()
        return $masters
    } catch {
        if ($reader) { $reader.Close() }
        if ($stream) { $stream.Close() }
        return @()
    }
}

function Get-CCDependencies {
    # Scan all enabled mods for CC dependencies
    $ccDependencies = @{}
    
    # Get active profile
    $profilesDir = "profiles"
    $mo2Ini = "ModOrganizer.ini"
    $activeProfile = "Default"
    
    if (Test-Path $mo2Ini) {
        $iniContent = Get-Content $mo2Ini
        foreach ($line in $iniContent) {
            if ($line -match 'selected_profile=(.+)') {
                $rawProfile = $matches[1].Trim()
                # Handle @ByteArray format: @ByteArray(ProfileName)
                if ($rawProfile -match '@ByteArray\((.+)\)') {
                    $activeProfile = $matches[1]
                } else {
                    $activeProfile = $rawProfile
                }
                break
            }
        }
    }
    
    $modlistPath = Join-Path $profilesDir "$activeProfile\modlist.txt"
    
    if (-not (Test-Path $modlistPath)) {
        return $ccDependencies
    }
    
    # Get list of enabled mods
    $modlistContent = Get-Content $modlistPath
    $enabledMods = @()
    
    foreach ($line in $modlistContent) {
        if ($line -match '^\+(.+)') {
            $enabledMods += $matches[1]
        }
    }
    
    # Scan each enabled mod for plugins
    foreach ($modName in $enabledMods) {
        $modPath = Join-Path $MO2ModsDir $modName
        if (-not (Test-Path $modPath)) { continue }
        
        # Find all plugin files in this mod
        $plugins = @()
        $plugins += Get-ChildItem -Path $modPath -Filter "*.esp" -File -ErrorAction SilentlyContinue
        $plugins += Get-ChildItem -Path $modPath -Filter "*.esm" -File -ErrorAction SilentlyContinue
        $plugins += Get-ChildItem -Path $modPath -Filter "*.esl" -File -ErrorAction SilentlyContinue
        
        foreach ($plugin in $plugins) {
            $masters = Get-PluginMasters -PluginPath $plugin.FullName
            
            foreach ($master in $masters) {
                # Check if this master is a CC file
                if ($master -match '^cc[a-z0-9]+\.es[lmp]$') {
                    $ccId = $master -replace '\.es[lmp]$', ''
                    
                    if (-not $ccDependencies.ContainsKey($ccId)) {
                        $ccDependencies[$ccId] = @()
                    }
                    
                    $ccDependencies[$ccId] += $modName
                }
            }
        }
    }
    
    return $ccDependencies
}

# ============================================
# Validation
# ============================================
if (-not (Test-Path "ModOrganizer.exe")) {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "ERROR: Mod Organizer 2 Not Found" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "This script must be run from your Mod Organizer 2 directory." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "1. Copy this script to your MO2 folder" -ForegroundColor Yellow
    Write-Host "2. Run it from there" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Example MO2 path: C:\Modding\MO2\" -ForegroundColor Gray
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path $Archive2Path)) {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "ERROR: Archive2.exe Not Found" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Archive2.exe is required for BA2 extraction." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "TO FIX:" -ForegroundColor Yellow
    Write-Host "1. Install Fallout 4 Creation Kit from Steam" -ForegroundColor Yellow
    Write-Host "2. Copy Archive2.exe from Creation Kit installation" -ForegroundColor Yellow
    Write-Host "   Location: [Creation Kit]\Tools\Archive2\Archive2.exe" -ForegroundColor Yellow
    Write-Host "3. Paste it in this folder: $PWD" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Alternative: Copy from Fallout 4 if available" -ForegroundColor Gray
    Write-Host "   Location: [Fallout 4]\Tools\Archive2\Archive2.exe" -ForegroundColor Gray
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Create log file if it doesn't exist
if (-not (Test-Path $LogFile)) {
    "BA2 Extraction Log" | Out-File -FilePath $LogFile
    "==================" | Out-File -FilePath $LogFile -Append
    "" | Out-File -FilePath $LogFile -Append
}

# ============================================
# Function: Count BA2 Files
# ============================================
function Count-BA2Files {
    Show-Header
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   Count BA2 Files (Total Load Order)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    # Get Fallout 4 installation path: prefer MO2 gamePath, fallback to registry
    $fo4Path = $null
    # Prefer MO2's configured gamePath if present (portable setups)
    $mo2IniPath = "ModOrganizer.ini"
    if (Test-Path $mo2IniPath) {
        try {
            $iniContent = Get-Content $mo2IniPath -ErrorAction Stop
            $gamePathLine = $iniContent | Where-Object { $_ -match '^gamePath=' }
            if ($gamePathLine) {
                if ($gamePathLine -match '@ByteArray\((.+)\)') {
                    $fo4Path = $matches[1] -replace '\\\\', '\\'
                } else {
                    $fo4Path = ($gamePathLine -replace '^gamePath=', '').Trim()
                }
            }
        } catch { }
    }
    # Fallback to registry if MO2 path not found
    if (-not $fo4Path) {
        try {
            $regKey = "HKLM:\SOFTWARE\WOW6432Node\Bethesda Softworks\Fallout4"
            if (Test-Path $regKey) {
                $fo4Path = (Get-ItemProperty -Path $regKey -Name "Installed Path" -ErrorAction SilentlyContinue)."Installed Path"
            }
        } catch {
            Write-Host "Warning: Could not read Fallout 4 registry path" -ForegroundColor Yellow
        }
    }

    # Read active CC plugins from Fallout4.ccc
    $activeCCPlugins = @()
    $cccPath = Join-Path $fo4Path "Fallout4.ccc"
    if (-not (Test-Path $cccPath)) {
        try {
            $cccCandidate = Get-ChildItem -Path $fo4Path -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -ieq 'Fallout4.ccc' } | Select-Object -First 1
            if ($cccCandidate) { $cccPath = $cccCandidate.FullName }
        } catch {}
    }
    if (Test-Path $cccPath) {
        $cccContent = Get-Content $cccPath
        foreach ($line in $cccContent) {
            $trimmedLine = $line.Trim()
            if ($trimmedLine -match '^cc.*\.es[lm]$') {
                # Remove extension to get base name for BA2 matching
                $pluginBase = $trimmedLine -replace '\.es[lm]$', ''
                $activeCCPlugins += $pluginBase
            }
        }
    }

    # Count base game BA2s and build list of vanilla BA2 names
    $baseGameCount = 0
    $ccCount = 0
    $dlcCount = 0
    $mainCount = 0
    $creationStoreCount = 0
    $vanillaBA2Names = @()

    if ($fo4Path -and (Test-Path $fo4Path)) {
        Write-Host "Scanning Fallout 4 Data folder..." -ForegroundColor Gray
        $dataPath = Join-Path $fo4Path "Data"
        if (-not (Test-Path $dataPath)) {
            try {
                $dataDir = Get-ChildItem -Path $fo4Path -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -ieq 'Data' } | Select-Object -First 1
                if ($dataDir) { $dataPath = $dataDir.FullName }
            } catch {}
        }
        if (Test-Path $dataPath) {
            $baseGameBA2s = Get-ChildItem -Path $dataPath -File | Where-Object { $_.Name -match '\.ba2$' }
            foreach ($ba2 in $baseGameBA2s) {
                $vanillaBA2Names += $ba2.Name.ToLower()
                
                # Categorize BA2 files
                if ($ba2.Name -like "cc*") {
                    # For CC BA2s, only count if the plugin is active in Fallout4.ccc
                    # Extract plugin base name from BA2 (e.g., "ccbgsfo4119-cyberdog - main.ba2" -> "ccbgsfo4119-cyberdog")
                    $ba2Base = $ba2.Name -replace ' - (main|textures)\.ba2$', ''
                    if ($activeCCPlugins -contains $ba2Base) {
                        $ccCount++
                        $baseGameCount++
                    }
                } elseif ($ba2.Name -like "DLC*") {
                    $dlcCount++
                    $baseGameCount++
                } elseif ($ba2.Name -like "Fallout4 - *") {
                    $mainCount++
                    $baseGameCount++
                } else {
                    # Creation Store Mods (encrypted, non-extractable)
                    $creationStoreCount++
                    $baseGameCount++
                }
            }
        }
    } else {
        Write-Host "Warning: Fallout 4 installation not found" -ForegroundColor Yellow
        Write-Host "Base game BA2s will not be counted" -ForegroundColor Yellow
    }

    # Count mod BA2s (excluding those that replace vanilla BA2s)
    $modCount = 0
    $replacementCount = 0
    Write-Host "Scanning MO2 mods folder..." -ForegroundColor Gray
    
    if (Test-Path $MO2ModsDir) {
        $modBA2s = Get-ChildItem -Path $MO2ModsDir -Recurse -File | Where-Object { $_.Name -match '\.ba2$' }
        foreach ($modBA2 in $modBA2s) {
            # Check if this mod BA2 replaces a vanilla BA2
            if ($vanillaBA2Names -contains $modBA2.Name.ToLower()) {
                $replacementCount++
            } else {
                $modCount++
            }
        }
    } else {
        Write-Host "Warning: Mods directory not found: $MO2ModsDir" -ForegroundColor Yellow
    }

    $total = $baseGameCount + $modCount

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "BA2 File Count Summary:" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Main Game Files:          $mainCount" -ForegroundColor White
    Write-Host "DLC Files:                $dlcCount" -ForegroundColor White
    Write-Host "Creation Club (CC):       $ccCount" -ForegroundColor White
    Write-Host "Creation Store Mods:      $creationStoreCount" -ForegroundColor White
    Write-Host "Mod BA2s (MO2):           $modCount" -ForegroundColor White
    if ($replacementCount -gt 0) {
        Write-Host "Vanilla Replacements:     $replacementCount" -ForegroundColor DarkGray -NoNewline
        Write-Host " (not counted)" -ForegroundColor DarkGray
    }
    Write-Host "----------------------------------------" -ForegroundColor Yellow
    Write-Host "TOTAL BA2 FILES:          " -NoNewline
    
    # Color the total based on safety thresholds
    if ($total -gt 500) {
        Write-Host "$total" -ForegroundColor Red
    } elseif ($total -gt 350) {
        Write-Host "$total" -ForegroundColor Yellow
    } else {
        Write-Host "$total" -ForegroundColor Green
    }
    
    Write-Host "----------------------------------------" -ForegroundColor Yellow
    Write-Host "Safe Limit:               350" -ForegroundColor Green
    Write-Host "Warning Zone:             350-500" -ForegroundColor Yellow
    Write-Host "Danger Zone:              500+" -ForegroundColor Red
    Write-Host ""
    Write-Host "WHAT THIS MEANS:" -ForegroundColor Cyan
    Write-Host "Think of BA2 files like boxes. Each box is packed full of game files like" -ForegroundColor White
    Write-Host "artwork, 3D models, sounds, and story text. Fallout 4 has to open each box" -ForegroundColor White
    Write-Host "when it starts up. The game can only handle opening so many boxes at once" -ForegroundColor White
    Write-Host "before it gets overwhelmed and crashes!" -ForegroundColor White
    Write-Host ""

    if ($total -gt 500) {
        Write-Host "STATUS: DANGER! Game will likely crash on startup!" -ForegroundColor Red
        Write-Host ""
        Write-Host "The game will most likely crash shortly after the music begins playing" -ForegroundColor Red
        Write-Host "and will not reach the menu. If you are seeing this behavior and you" -ForegroundColor Red
        Write-Host "have over 500 on this count, it is most likely the cause." -ForegroundColor Red
        Write-Host ""
    Write-Host "What should you do next to keep the game from crashing?" -ForegroundColor Yellow
    Write-Host "1. Go back to the main menu" -ForegroundColor White
    Write-Host "2. Choose option 2 (Manage BA2 Mods)" -ForegroundColor White
        Write-Host "3. Extract BA2s to get as close to 350 as you can" -ForegroundColor White
        Write-Host ""
        Write-Host "Don't worry! This is safe and can be undone later." -ForegroundColor Green
    } elseif ($total -gt 350) {
        Write-Host "STATUS: WARNING! You're in the danger zone!" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "You're getting close to the crash limit. The game might still work," -ForegroundColor Yellow
        Write-Host "but you're more likely to experience crashes, freezes, or other problems." -ForegroundColor Yellow
        Write-Host ""
    Write-Host "What you should do:" -ForegroundColor Cyan
    Write-Host "1. Go back to the main menu" -ForegroundColor White
    Write-Host "2. Choose option 2 (Manage BA2 Mods)" -ForegroundColor White
        Write-Host "3. Extract BA2s to get as close to 350 as you can" -ForegroundColor White
        Write-Host ""
        Write-Host "The sooner you do this, the better!" -ForegroundColor Yellow
    } else {
        Write-Host "STATUS: Looking good! You should be safe." -ForegroundColor Green
        Write-Host ""
        Write-Host "Your BA2 count is within safe limits. The game should run fine" -ForegroundColor Gray
        Write-Host "without any BA2-related crashes or issues." -ForegroundColor Gray
        Write-Host ""
        Write-Host "You can safely add about $([Math]::Max(0, 350 - $total)) more BA2 files before hitting the warning zone." -ForegroundColor Gray
    }

    Write-Host ""
    Read-Host "Press Enter to go back to the main menu"
}

# ============================================
# Global: Track failed extractions
# ============================================
$script:FailedExtractions = @()

# Load failed extractions from file if it exists
if (Test-Path $FailedExtractionsFile) {
    try {
        $script:FailedExtractions = @(Get-Content $FailedExtractionsFile)
    } catch {
        # If file is corrupt or can't be read, start fresh
        $script:FailedExtractions = @()
    }
}

# Helper function to save failed extractions to file
function Save-FailedExtractions {
    try {
        $script:FailedExtractions | Set-Content $FailedExtractionsFile -Force
    } catch {
        Write-Log "ERROR|Failed to save failed extractions file: $_"
    }
}

# ============================================
# Helper Function: Parse number ranges
# ============================================
function Parse-NumberRanges {
    param(
        [string]$inputString,
        [int]$maxValue
    )
    
    $result = @()
    $parts = $inputString -split ',' | ForEach-Object { $_.Trim() }
    
    foreach ($part in $parts) {
        if ($part -match '^(\d+)-(\d+)$') {
            # Range format: "1-5"
            $start = [int]$matches[1]
            $end = [int]$matches[2]
            
            if ($start -gt $end) {
                # Swap if reversed
                $temp = $start
                $start = $end
                $end = $temp
            }
            
            for ($i = $start; $i -le $end; $i++) {
                if ($i -ge 1 -and $i -le $maxValue) {
                    $result += $i
                }
            }
        }
        elseif ($part -match '^\d+$') {
            # Single number
            $num = [int]$part
            if ($num -ge 1 -and $num -le $maxValue) {
                $result += $num
            }
        }
    }
    
    return ($result | Select-Object -Unique | Sort-Object)
}

# ============================================
# Function: Manage BA2 Mods (Extract/Restore)
# ============================================
function Manage-BA2Mods {
    # Initialize pagination state (persists across rescans)
    $currentPage = 0
    $pageSize = 20
    
    while ($true) {
        Show-Header
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "   Manage BA2 Mods - Current Status" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
    
    # Count current BA2 files from both game and mods
    $baseGameCount = 0
    $modCount = 0
    
    # Get Fallout 4 installation path: prefer MO2 gamePath, fallback to registry
    $fo4Path = $null
    $mo2IniPath = "ModOrganizer.ini"
    if (Test-Path $mo2IniPath) {
        try {
            $iniContent = Get-Content $mo2IniPath -ErrorAction Stop
            $gamePathLine = $iniContent | Where-Object { $_ -match '^gamePath=' }
            if ($gamePathLine) {
                if ($gamePathLine -match '@ByteArray\((.+)\)') {
                    $fo4Path = $matches[1] -replace '\\\\', '\\'
                } else {
                    $fo4Path = ($gamePathLine -replace '^gamePath=', '').Trim()
                }
            }
        } catch { }
    }
    if (-not $fo4Path) {
        try {
            $regKey = "HKLM:\SOFTWARE\WOW6432Node\Bethesda Softworks\Fallout4"
            if (Test-Path $regKey) {
                $fo4Path = (Get-ItemProperty -Path $regKey -Name "Installed Path" -ErrorAction SilentlyContinue)."Installed Path"
            }
        } catch { }
    }
    
    # Read active CC plugins from Fallout4.ccc
    $activeCCPlugins = @()
    $cccPath = Join-Path $fo4Path "Fallout4.ccc"
    if (Test-Path $cccPath) {
        $cccContent = Get-Content $cccPath
        foreach ($line in $cccContent) {
            $trimmedLine = $line.Trim()
            if ($trimmedLine -match '^cc.*\.es[lm]$') {
                $pluginBase = $trimmedLine -replace '\.es[lm]$', ''
                $activeCCPlugins += $pluginBase
            }
        }
    }

    # Count base game BA2s and build list of vanilla names
    $vanillaBA2Names = @()
    if ($fo4Path -and (Test-Path $fo4Path)) {
        $dataPath = Join-Path $fo4Path "Data"
        if (Test-Path $dataPath) {
            $vanillaBA2s = Get-ChildItem -Path $dataPath -Filter "*.ba2" -File
            $vanillaBA2Names = $vanillaBA2s | ForEach-Object { $_.Name.ToLower() }
            
            # Count only active CC BA2s
            foreach ($ba2 in $vanillaBA2s) {
                if ($ba2.Name -like "cc*") {
                    $ba2Base = $ba2.Name -replace ' - (main|textures)\.ba2$', ''
                    if ($activeCCPlugins -contains $ba2Base) {
                        $baseGameCount++
                    }
                } else {
                    $baseGameCount++
                }
            }
        }
    }
    
    # Count mod BA2s (excluding vanilla replacements)
    $modCount = 0
    if (Test-Path $MO2ModsDir) {
        $modBA2s = Get-ChildItem -Path $MO2ModsDir -Recurse -Filter "*.ba2" -File
        foreach ($modBA2 in $modBA2s) {
            if ($vanillaBA2Names -notcontains $modBA2.Name.ToLower()) {
                $modCount++
            }
        }
    }
    
    $currentBA2Count = $baseGameCount + $modCount
    
    # Get all mod folders with BA2 files OR backups (extracted mods)
    $modFolders = Get-ChildItem -Path $MO2ModsDir -Directory
    $allMods = @()
    
    # Build list of mods with BA2 files (not extracted)
    foreach ($modFolder in $modFolders) {
        $ba2Files = Get-ChildItem -Path $modFolder.FullName -File | Where-Object { $_.Name -match '\.ba2$' }
        
        # Filter out BA2s that replace vanilla files
        $nonVanillaBA2s = @()
        foreach ($ba2 in $ba2Files) {
            if ($vanillaBA2Names -notcontains $ba2.Name.ToLower()) {
                $nonVanillaBA2s += $ba2
            }
        }
        
        if ($nonVanillaBA2s.Count -gt 0) {
            # Try to read meta.ini for Nexus URL
            $metaIniPath = Join-Path $modFolder.FullName "meta.ini"
            $nexusUrl = $null
            if (Test-Path $metaIniPath) {
                try {
                    $metaLines = Get-Content $metaIniPath
                    $modid = $null
                    $gameName = $null
                    $repository = $null
                    
                    foreach ($line in $metaLines) {
                        if ($line -match '^modid=(.+)$') {
                            $modid = $matches[1].Trim()
                        }
                        elseif ($line -match '^gameName=(.+)$') {
                            $gameName = $matches[1].Trim()
                        }
                        elseif ($line -match '^repository=(.+)$') {
                            $repository = $matches[1].Trim()
                        }
                    }
                    
                    # Construct URL from modid if it's from Nexus
                    if ($modid -and $repository -eq 'Nexus' -and $gameName) {
                        $gameNameLower = $gameName.ToLower()
                        $nexusUrl = "https://www.nexusmods.com/$gameNameLower/mods/$modid"
                    }
                } catch {
                    # Ignore errors reading meta.ini
                }
            }
            
            $allMods += @{
                Name = $modFolder.Name
                Path = $modFolder.FullName
                BA2Count = $nonVanillaBA2s.Count
                BA2Files = $nonVanillaBA2s
                NexusUrl = $nexusUrl
                IsExtracted = $false
            }
        }
    }
    
    # Add extracted mods (those with backups)
    if (Test-Path $BackupDir) {
        $backupFolders = Get-ChildItem -Path $BackupDir -Directory
        foreach ($backupFolder in $backupFolders) {
            # Check if this mod is already in our list (has BA2s)
            $existingMod = $allMods | Where-Object { $_.Name -eq $backupFolder.Name }
            if (-not $existingMod) {
                # This is an extracted mod
                $allMods += @{
                    Name = $backupFolder.Name
                    Path = (Join-Path $MO2ModsDir $backupFolder.Name)
                    BA2Count = 0
                    BA2Files = @()
                    NexusUrl = $null
                    IsExtracted = $true
                }
            }
        }
    }
    
    # Keep alphabetical order - don't move extracted mods to bottom
    $allMods = $allMods | Sort-Object { $_.Name } -Culture "en-US"
    
    if ($allMods.Count -eq 0) {
        Show-Header
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "   Manage BA2 Mods" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "No mods with BA2 files or extracted mods found!" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to continue"
        return
    }
    
    # Calculate pagination for current mod list
    $totalPages = [Math]::Ceiling($allMods.Count / $pageSize)
    
    # Ensure current page is within bounds (mod list may have changed)
    if ($currentPage -ge $totalPages) {
        $currentPage = [Math]::Max(0, $totalPages - 1)
    }
    
    # Pagination and action loop
    while ($true) {
        $selection = ""
        Show-Header
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "   Manage BA2 Mods" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Show-BA2Count -Count $currentBA2Count
        Write-Host ""
        Write-Host "Select mods to EXTRACT or RESTORE (supports ranges: 1-5,8,10-12):" -ForegroundColor Yellow
        Write-Host "  - To RESTORE all extracted mods, type " -ForegroundColor White -NoNewline
        Write-Host "restore" -ForegroundColor Green
        Write-Host ""
        Write-Host "Page $($currentPage + 1) of $totalPages" -ForegroundColor Cyan
        Write-Host ""
        
        # Display current page
        $startIdx = $currentPage * $pageSize
        $endIdx = [Math]::Min($startIdx + $pageSize, $allMods.Count)
        
        for ($i = $startIdx; $i -lt $endIdx; $i++) {
            $mod = $allMods[$i]
            $isFailed = $script:FailedExtractions -contains $mod.Name
            
            Write-Host "  [$($i + 1)] " -ForegroundColor Yellow -NoNewline
            
            if ($mod.IsExtracted) {
                # Extracted mod - show in green with indicator
                Write-Host "(EXTRACTED) " -ForegroundColor Green -NoNewline
                Write-Host "$($mod.Name) " -ForegroundColor Green -NoNewline
                Write-Host "(0 BA2 files)" -ForegroundColor DarkGray -NoNewline
            } elseif ($isFailed) {
                Write-Host "$($mod.Name) " -ForegroundColor Red -NoNewline
                Write-Host "($($mod.BA2Count) BA2 file(s)) " -ForegroundColor DarkGray -NoNewline
                Write-Host "[EXTRACTION FAILED - ROLLED BACK]" -ForegroundColor Red -NoNewline
            } else {
                Write-Host "$($mod.Name) " -ForegroundColor White -NoNewline
                Write-Host "($($mod.BA2Count) BA2 file(s))" -ForegroundColor DarkGray -NoNewline
            }
            
            if ($mod.NexusUrl) {
                Write-Host " - " -NoNewline -ForegroundColor DarkGray
                Write-Host "$($mod.NexusUrl)" -ForegroundColor Cyan
            } else {
                Write-Host ""
            }
        }
        
        Write-Host ""
        Write-Host "----------------------------------------" -ForegroundColor DarkGray
        
        # Navigation options
        if ($totalPages -gt 1) {
            Write-Host "Navigation: " -NoNewline -ForegroundColor White
            Write-Host "n" -NoNewline -ForegroundColor Yellow
            Write-Host "=Next 20 | " -NoNewline -ForegroundColor White
            Write-Host "p" -NoNewline -ForegroundColor Yellow
            Write-Host "=Previous 20 | " -NoNewline -ForegroundColor White
            Write-Host "h" -NoNewline -ForegroundColor Yellow
            Write-Host "=First page | " -NoNewline -ForegroundColor White
            Write-Host "e" -NoNewline -ForegroundColor Yellow
            Write-Host "=Last page | " -NoNewline -ForegroundColor White
            Write-Host "q" -NoNewline -ForegroundColor Yellow
            Write-Host "=Quit" -ForegroundColor White
            Write-Host "Type a number or range like 1-5,8,10-12 (or 'restore')" -ForegroundColor White
        } else {
            Write-Host "Type a number or range like 1-5,8,10-12, or " -NoNewline -ForegroundColor White
            Write-Host "q" -NoNewline -ForegroundColor Yellow
            Write-Host " to return to main menu" -ForegroundColor White
        }
        Write-Host "Enter your selection or press Enter to cancel" -ForegroundColor White
        Write-Host ""
        
        $userInput = Read-Host "Your choice"
        
        # Handle navigation
        $inputLower = $userInput.Trim().ToLower()
        if ($inputLower -eq 'n' -and $currentPage -lt ($totalPages - 1)) {
            $currentPage++
            continue
        } elseif ($inputLower -eq 'p' -and $currentPage -gt 0) {
            $currentPage--
            continue
        } elseif ($inputLower -eq 'h') {
            $currentPage = 0
            continue
        } elseif ($inputLower -eq 'e') {
            $currentPage = $totalPages - 1
            continue
        } elseif ($inputLower -eq 'q' -or [string]::IsNullOrWhiteSpace($userInput)) {
            return
        } else {
            # Treat as selection
            $selection = $userInput
            break  # leave pagination loop and perform action
        }
    }

    # At this point we have a selection (or keyword) and want to perform an action,
    # then return to this same while($true) to rebuild the list unless the user quits.

    # Check for special keyword: restore
    $inputLower = $selection.ToLower().Trim()
    
    if ($inputLower -eq 'restore') {
        # Restore ALL extracted mods
        $modsToRestore = $allMods | Where-Object { $_.IsExtracted }
        $modsToExtract = @()
        
        if ($modsToRestore.Count -eq 0) {
            Write-Host "No extracted mods to restore!" -ForegroundColor Yellow
            Start-Sleep -Seconds 2
            continue  # back to list
        }
        
        # Calculate total BA2 files that will be restored
        $totalBA2s = 0
        foreach ($mod in $modsToRestore) {
            $totalBA2s += $mod.BA2Count
        }
        
        Write-Host ""
        Write-Host "RESTORE ALL EXTRACTED MODS" -ForegroundColor Green
        Write-Host "This will restore all $($modsToRestore.Count) extracted mods (~$totalBA2s BA2 files)" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Ready to restore ALL? Type " -NoNewline
        Write-Host "yes" -ForegroundColor Green -NoNewline
        Write-Host " to continue (any other key to cancel)"
        $confirm = Read-Host
        
        if ($confirm -ne 'yes') {
            Write-Host "Cancelled. Returning to BA2 mod list..." -ForegroundColor Yellow
            Start-Sleep -Seconds 2
            continue
        }
        
        # Convert to the format expected by restore logic
        $modsToRestore = $modsToRestore | ForEach-Object { @{ Mod = $_ } }
        $modsToExtract = @()
    }
    else {
        # Parse selection (supports ranges like "1-5,8,10-12")
        $selectedIndices = @()
        try {
            $numbers = Parse-NumberRanges -inputString $selection -maxValue $allMods.Count
            foreach ($num in $numbers) {
                $selectedIndices += ($num - 1)  # Convert to 0-based index
            }
        } catch {
            Write-Host "Invalid input! Use format: 1-5,8,10-12" -ForegroundColor Red
            Start-Sleep -Seconds 2
            continue
        }
        
        if ($selectedIndices.Count -eq 0) {
            Write-Host "No valid selections." -ForegroundColor Yellow
            Start-Sleep -Seconds 2
            continue
        }
        
        # Separate extracted and non-extracted mods
        $modsToExtract = @()
        $modsToRestore = @()
        
        foreach ($idx in $selectedIndices) {
            $mod = $allMods[$idx]
            if ($mod.IsExtracted) {
                $modsToRestore += @{ Index = $idx; Mod = $mod }
            } else {
                $modsToExtract += @{ Index = $idx; Mod = $mod }
            }
        }
    }
    
    # Show what will happen
    Write-Host ""
    if ($modsToExtract.Count -gt 0) {
        Write-Host "Mods to EXTRACT ($($modsToExtract.Count)):" -ForegroundColor Yellow
        foreach ($item in $modsToExtract) {
            Write-Host "  - $($item.Mod.Name) ($($item.Mod.BA2Count) BA2 file(s))" -ForegroundColor White
            if ($item.Mod.NexusUrl) {
                Write-Host "    $($item.Mod.NexusUrl)" -ForegroundColor Cyan
            }
        }
        Write-Host ""
    }
    
    if ($modsToRestore.Count -gt 0) {
        Write-Host "Mods to RESTORE ($($modsToRestore.Count)):" -ForegroundColor Green
        foreach ($item in $modsToRestore) {
            Write-Host "  - $($item.Mod.Name)" -ForegroundColor Green
        }
        Write-Host ""
    }
    
    Write-Host "Ready to proceed? Type " -NoNewline
    Write-Host "y" -ForegroundColor Green -NoNewline
    Write-Host " to continue or " -NoNewline
    Write-Host "n" -ForegroundColor Red -NoNewline
    Write-Host " to cancel"
    $confirm = Read-Host
    
    if ($confirm -ne 'y') {
        Write-Host "Cancelled. Returning to BA2 mod list..." -ForegroundColor Yellow
        Start-Sleep -Seconds 2
        continue
    }
    
    # Process extractions first
    if ($modsToExtract.Count -gt 0) {
        Write-Log "BEGIN EXTRACTION"
        
        # Create backup directory if it doesn't exist
        if (-not (Test-Path $BackupDir)) {
            New-Item -Path $BackupDir -ItemType Directory | Out-Null
        }
        
        $extractedCount = 0
        
        # Process mods to extract
        foreach ($item in $modsToExtract) {
            $mod = $item.Mod
        $modName = $mod.Name
        $modPath = $mod.Path
        $ba2Files = $mod.BA2Files
        
        Write-Host ""
        Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
        Write-Host "PROCESSING: $modName" -ForegroundColor Cyan
        Write-Host ""

        # Check if backup already exists
        $backupPath = Join-Path $BackupDir $modName
        if (Test-Path $backupPath) {
            Write-Host "  Deleting old backup..." -ForegroundColor Gray
            Remove-Item -Path $backupPath -Recurse -Force
        }

        # Step 1: Create full backup of mod folder
        try {
            Write-Host "  [Step 1/3] Making a complete backup of your mod..." -ForegroundColor Cyan
            Copy-Item -Path $modPath -Destination $backupPath -Recurse -Force
            Write-Host "  [OK] Backup saved to: mod_backups\$modName" -ForegroundColor Green
            Write-Log "BACKUP_CREATED|$modName|$(Get-Date)"
        } catch {
            Write-Host "  [ERROR] Failed to create backup: $_" -ForegroundColor Red
            Write-Log "ERROR|BACKUP_FAILED|$modName|$_"
            continue
        }

        # Step 2: Extract each BA2 in this mod
        Write-Host "  [Step 2/3] Unpacking BA2 files..." -ForegroundColor Cyan
        $ba2List = @()
        $extractionFailed = $false
        
        foreach ($ba2File in $ba2Files) {
            $ba2Name = $ba2File.Name
            Write-Host "    Opening: $ba2Name" -ForegroundColor Gray
            
            try {
                $process = Start-Process -FilePath $Archive2Path -ArgumentList "`"$($ba2File.FullName)`"", "-extract=`"$modPath`"" -NoNewWindow -Wait -PassThru
                
                if ($process.ExitCode -eq 0) {
                    Write-Host "    [OK] Unpacked successfully!" -ForegroundColor Green
                    $ba2List += $ba2Name
                } else {
                    Write-Host "    [ERROR] Failed to unpack $ba2Name" -ForegroundColor Red
                    Write-Log "ERROR|EXTRACT_FAILED|$modName|$ba2Name"
                    $extractionFailed = $true
                }
            } catch {
                Write-Host "    [ERROR] Failed to unpack $ba2Name : $_" -ForegroundColor Red
                Write-Log "ERROR|EXTRACT_FAILED|$modName|$ba2Name|$_"
                $extractionFailed = $true
            }
        }

        # Check if any extraction failed
        if ($extractionFailed) {
            Write-Host ""
            Write-Host "  [ROLLBACK] Extraction failed - restoring from backup..." -ForegroundColor Yellow
            try {
                # Delete the mod folder (which may have partial extraction)
                if (Test-Path $modPath) {
                    Remove-Item -Path $modPath -Recurse -Force
                }
                # Restore from backup
                if (Test-Path $backupPath) {
                    Copy-Item -Path $backupPath -Destination $modPath -Recurse -Force
                    Write-Host "  [OK] Mod restored to original state" -ForegroundColor Green
                } else {
                    Write-Host "  [ERROR] Backup path not found!" -ForegroundColor Red
                }
                Write-Log "ROLLBACK_SUCCESS|$modName|$(Get-Date)"
            } catch {
                Write-Host "  [ERROR] Rollback failed: $_" -ForegroundColor Red
                Write-Log "ERROR|ROLLBACK_FAILED|$modName|$_"
            }
            
            # Add to failed extractions list
            $script:FailedExtractions += $modName
            Save-FailedExtractions
            continue
        }

        # Step 3: Delete BA2 files from mod (backup has originals)
        if ($ba2List.Count -gt 0) {
            Write-Host "  [Step 3/3] Removing empty BA2 boxes from mod..." -ForegroundColor Cyan
            foreach ($ba2File in $ba2Files) {
                Remove-Item -Path $ba2File.FullName -Force
            }
            Write-Host "  [OK] Done! BA2 files removed (originals safe in backup)" -ForegroundColor Green
            Write-Host ""
            Write-Host "  This mod now counts as 0 BA2 files instead of $($ba2List.Count)!" -ForegroundColor Yellow
            Write-Log "BA2_EXTRACTED|$modName|$($ba2List -join ',')|$(Get-Date)"
            $extractedCount++
            
            # Recalculate current BA2 count (excluding vanilla replacements)
            $modCount = 0
            if (Test-Path $MO2ModsDir) {
                $modBA2s = Get-ChildItem -Path $MO2ModsDir -Recurse -File | Where-Object { $_.Name -match '\.ba2$' }
                foreach ($modBA2 in $modBA2s) {
                    if ($vanillaBA2Names -notcontains $modBA2.Name.ToLower()) {
                        $modCount++
                    }
                }
            }
            $currentBA2Count = $baseGameCount + $modCount
            
            # Refresh screen with updated count
            Show-Header
            Write-Host "========================================" -ForegroundColor Cyan
            Write-Host "   Extracting BA2s - In Progress" -ForegroundColor Cyan
            Write-Host "========================================" -ForegroundColor Cyan
            Write-Host ""
            Show-BA2Count -Count $currentBA2Count
        }
    }

        Write-Log "END EXTRACTION"
    }
    
    # Process restores
    if ($modsToRestore.Count -gt 0) {
        Write-Log "BEGIN RESTORE"
        
        $restoredCount = 0
        
        foreach ($item in $modsToRestore) {
            $mod = $item.Mod
            $modName = $mod.Name
            
            Write-Host ""
            Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
            Write-Host "RESTORING: $modName" -ForegroundColor Cyan
            Write-Host ""
            
            $modPath = Join-Path $MO2ModsDir $modName
            $backupPath = Join-Path $BackupDir $modName
            
            if (-not (Test-Path $backupPath)) {
                Write-Host "  [ERROR] Backup not found! Cannot restore." -ForegroundColor Red
                Write-Log "ERROR|RESTORE_NO_BACKUP|$modName"
                continue
            }
            
            # Step 1: Delete current mod folder
            if (Test-Path $modPath) {
                try {
                    Write-Host "  [Step 1/2] Deleting the unpacked version..." -ForegroundColor Cyan
                    Remove-Item -Path $modPath -Recurse -Force
                    Write-Host "  [OK] Unpacked version removed" -ForegroundColor Green
                } catch {
                    Write-Host "  [ERROR] Something went wrong deleting the mod: $_" -ForegroundColor Red
                    Write-Log "ERROR|DELETE_FAILED|$modName|$_"
                    continue
                }
            }
            
            # Step 2: Move backup to mods folder
            try {
                Write-Host "  [Step 2/2] Bringing back the original with BA2 files..." -ForegroundColor Cyan
                Move-Item -Path $backupPath -Destination $modPath -Force
                Write-Host "  [OK] Mod restored! BA2 files are back." -ForegroundColor Green
                Write-Host ""
                Write-Host "  This mod now counts toward the BA2 limit again." -ForegroundColor Yellow
                Write-Log "RESTORED|$modName|$(Get-Date)"
                
                # Remove from failed extractions list if present
                if ($script:FailedExtractions -contains $modName) {
                    $script:FailedExtractions = $script:FailedExtractions | Where-Object { $_ -ne $modName }
                    Save-FailedExtractions
                }
                
                $restoredCount++
            } catch {
                Write-Host "  [ERROR] Something went wrong restoring the mod: $_" -ForegroundColor Red
                Write-Log "ERROR|RESTORE_FAILED|$modName|$_"
            }
        }
        
        Write-Log "END RESTORE"
    }
    
    # Show summary
    Write-Host ""
    Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "ALL DONE!" -ForegroundColor Green
    Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "SUMMARY:" -ForegroundColor Cyan
    
    if ($modsToExtract.Count -gt 0) {
        Write-Host "  Mods successfully extracted: $extractedCount" -ForegroundColor White
        
        if ($script:FailedExtractions.Count -gt 0) {
            Write-Host "  Mods with extraction failures: $($script:FailedExtractions.Count)" -ForegroundColor Red
        }
    }
    
    if ($modsToRestore.Count -gt 0) {
        Write-Host "  Mods successfully restored: $restoredCount" -ForegroundColor White
    }
    
    if ($script:FailedExtractions.Count -gt 0 -and $modsToExtract.Count -gt 0) {
        Write-Host ""
        Write-Host "FAILED EXTRACTIONS (rolled back to BA2):" -ForegroundColor Red
        foreach ($failedMod in $script:FailedExtractions) {
            Write-Host "  - $failedMod" -ForegroundColor Red
        }
        Write-Host ""
        Write-Host "These mods have been restored to their original BA2 state." -ForegroundColor Yellow
        Write-Host "Check the extraction log for details about the failures." -ForegroundColor Yellow
    }
    
        Write-Host ""
        $response = (Read-Host "Press Enter to return to your page, or type 'q' to return to main menu").Trim().ToLower()
        if ($response -eq 'q') {
            return
        }
        
        # Re-scan mods to update states, but stay on current page
        # This continues the outer function loop which rebuilds the mod list
        # but we preserve $currentPage so user returns to their page
        continue  # Continue outer loop to rebuild mod list
    }
}

# ============================================
# Function: View Log
# ============================================
function View-Log {
    Show-Header
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   Extraction Log" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    if (-not (Test-Path $LogFile)) {
        Write-Host "No log file found." -ForegroundColor Yellow
        Write-Host "Extract some BA2s first." -ForegroundColor Yellow
    } else {
        Get-Content -Path $LogFile | Write-Host
    }

    Write-Host ""
    Read-Host "Press Enter to continue"
}

# ============================================
# ============================================
# Function: Manage Creation Club Content
# ============================================
function Manage-CreationClub {
    # Initialize pagination state (persists across rescans)
    $currentPage = 0
    $pageSize = 20
    
    while ($true) {
        Show-Header
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "   Manage Creation Club Content" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
    
    # Prefer MO2's gamePath if available, else registry
    $fo4Path = $null
    try {
        $mo2IniPath = "ModOrganizer.ini"
        if (Test-Path $mo2IniPath) {
            $iniContent = Get-Content $mo2IniPath -ErrorAction Stop
            $gamePathLine = $iniContent | Where-Object { $_ -match '^gamePath=' }
            if ($gamePathLine) {
                if ($gamePathLine -match '@ByteArray\((.+)\)') {
                    $fo4Path = $matches[1] -replace '\\\\', '\\'
                } else {
                    $fo4Path = ($gamePathLine -replace '^gamePath=', '').Trim()
                }
            }
        }
        if (-not $fo4Path) {
            $fo4Path = (Get-ItemProperty -Path "HKLM:\SOFTWARE\WOW6432Node\Bethesda Softworks\Fallout4" -Name "Installed Path" -ErrorAction Stop)."Installed Path"
        }
    } catch { }
    
    if (-not $fo4Path) {
        Write-Host "Cannot find Fallout 4 installation!" -ForegroundColor Red
        Write-Host ""
        Read-Host "Press Enter to continue"
        return
    }
    
    $fo4DataPath = Join-Path $fo4Path "Data"
    if (-not (Test-Path $fo4DataPath)) {
        try {
            $dataDir = Get-ChildItem -Path $fo4Path -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -ieq 'Data' } | Select-Object -First 1
            if ($dataDir) { $fo4DataPath = $dataDir.FullName }
        } catch {}
    }
    
    # Check for Fallout4.ccc file
    $cccPath = Join-Path $fo4Path "Fallout4.ccc"
    if (-not (Test-Path $cccPath)) {
        Write-Host "Cannot find Fallout4.ccc file!" -ForegroundColor Red
        try {
            $cccCandidate = Get-ChildItem -Path $fo4Path -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -ieq 'Fallout4.ccc' } | Select-Object -First 1
            if ($cccCandidate) { $cccPath = $cccCandidate.FullName }
        } catch {}
        if (-not (Test-Path $cccPath)) {
            Write-Host "Expected location: $(Join-Path $fo4Path 'Fallout4.ccc')" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "This file is required to manage Creation Club content." -ForegroundColor White
            Write-Host ""
            Read-Host "Press Enter to continue"
            return
        }
    }
    
    # Create or update master backup
    $masterBackupPath = "$cccPath.master_backup"
    
    if (-not (Test-Path $masterBackupPath)) {
        # No master backup exists - create one
        Copy-Item $cccPath $masterBackupPath -Force
        Write-Host "Created master backup: Fallout4.ccc.master_backup" -ForegroundColor Green
        Write-Host "This backup can be used to restore all CC content at once." -ForegroundColor White
        Write-Host ""
        Write-Log "CC_MASTER_BACKUP_CREATED|FirstTime|$(Get-Date)"
    } else {
        # Check if current .ccc has more CC content than backup
        $currentCCC = Get-Content $cccPath
        $backupCCC = Get-Content $masterBackupPath
        
        # Count CC entries (lines starting with 'cc' and ending with .esl or .esm)
        $currentCCCount = ($currentCCC | Where-Object { $_ -match '^cc.*\.es[lm]$' }).Count
        $backupCCCount = ($backupCCC | Where-Object { $_ -match '^cc.*\.es[lm]$' }).Count
        
        if ($currentCCCount -gt $backupCCCount) {
            # New CC content detected - update backup
            $newItems = $currentCCCount - $backupCCCount
            Write-Host "Detected $newItems new CC item(s)! Updating master backup..." -ForegroundColor Yellow
            
            # 1. Rename current to .tmp
            $tmpPath = "$cccPath.tmp"
            Move-Item $cccPath $tmpPath -Force
            
            # 2. Restore backup to main location
            Copy-Item $masterBackupPath $cccPath -Force
            
            # 3. Find new items (in tmp but not in backup)
            $tmpCCC = Get-Content $tmpPath
            $newCCItems = @()
            foreach ($line in $tmpCCC) {
                if ($line -match '^cc.*\.es[lm]$' -and $backupCCC -notcontains $line) {
                    $newCCItems += $line
                }
            }
            
            # 4. Add new items to current ccc
            $currentCCC = Get-Content $cccPath
            $currentCCC += $newCCItems
            $currentCCC | Set-Content $cccPath -Encoding ASCII
            
            # 5. Update master backup with new items
            Copy-Item $cccPath $masterBackupPath -Force
            
            # 6. Restore tmp back to main ccc
            Move-Item $tmpPath $cccPath -Force
            
            Write-Host "Master backup updated with $newItems new CC item(s)" -ForegroundColor Green
            Write-Host ""
            Write-Log "CC_MASTER_BACKUP_UPDATED|NewItems:$newItems|$(Get-Date)"
        }
    }
    
    # Read active CC plugins from Fallout4.ccc
    $cccContent = Get-Content $cccPath
    $activeCCPlugins = @()
    foreach ($line in $cccContent) {
        $trimmedLine = $line.Trim()
        if ($trimmedLine -match '^cc.*\.es[lm]$') {
            $activeCCPlugins += $trimmedLine
        }
    }
    
    # Scan Data folder for ALL CC plugins (not just active ones)
    $allCCPlugins = @()
    if (Test-Path $fo4DataPath) {
        # Get both .esl and .esm files (Filter doesn't support regex [lm])
        $ccPluginFiles = Get-ChildItem -Path $fo4DataPath -File | Where-Object { $_.Name -match '^cc.*\.es[lm]$' }
        foreach ($pluginFile in $ccPluginFiles) {
            $allCCPlugins += $pluginFile.Name
        }
    }
    
    # Sort alphabetically - don't move disabled to bottom
    $allCCPlugins = $allCCPlugins | Select-Object -Unique | Sort-Object
    
    if ($allCCPlugins.Count -eq 0) {
        Write-Host "No Creation Club content found in Data folder!" -ForegroundColor Yellow
        Write-Host "Expected location: $fo4DataPath" -ForegroundColor White
        Write-Host ""
        Read-Host "Press Enter to continue"
        return
    }
    
    # Count active and disabled CC
    $activeCount = $activeCCPlugins.Count
    $disabledCount = $allCCPlugins.Count - $activeCount
    $ccBA2Count = $activeCount * 2
    
    Write-Host "Found $($allCCPlugins.Count) total CC items: " -ForegroundColor Cyan -NoNewline
    Write-Host "$activeCount active" -ForegroundColor Green -NoNewline
    Write-Host ", " -NoNewline
    Write-Host "$disabledCount disabled" -ForegroundColor DarkGray
    Write-Host "Active CC items use ~$ccBA2Count BA2 files" -ForegroundColor Cyan
    Write-Host ""
    
    # Build full CC list with metadata from ALL plugins
    $ccList = @()
    $index = 1
    foreach ($plugin in $allCCPlugins) {
        $friendlyName = "Unknown"
        $isActive = $activeCCPlugins -contains $plugin
        
        # Extract the base ID from plugin name (e.g., ccBGSFO4001-PipBoy(Black).esl -> ccbgsfo4001)
        $pluginBase = $plugin -replace '\.es[lm]$', ''  # Remove extension
        $baseId = ($pluginBase -replace '[-_].*$', '').ToLower()  # Remove suffix after - or _, lowercase
        $ba2Count = 2  # Default
        
        if ($CCNames.ContainsKey($baseId)) {
            $ccInfo = $CCNames[$baseId]
            $friendlyName = $ccInfo.Name
            $ba2Count = $ccInfo.BA2Count
        }
        
        $ccList += @{
            Index = $index
            PluginName = $plugin
            BaseId = $baseId
            FriendlyName = $friendlyName
            BA2Count = $ba2Count
            IsActive = $isActive
        }
        
        $index++
    }
    
    # Sort alphabetically by friendly name
    $ccList = $ccList | Sort-Object { $_.FriendlyName } -Culture "en-US"
    
    # Re-index after sorting
    for ($i = 0; $i -lt $ccList.Count; $i++) {
        $ccList[$i].Index = $i + 1
    }
    
    # Calculate pagination for current CC list
    $totalPages = [Math]::Ceiling($ccList.Count / $pageSize)
    
    # Ensure current page is within bounds (CC list may have changed)
    if ($currentPage -ge $totalPages) {
        $currentPage = [Math]::Max(0, $totalPages - 1)
    }
    
    $selection = ""
    
    # Pagination loop
    while ($true) {
        Show-Header
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "   Manage Creation Club Content" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Select CC items by number to ENABLE/DISABLE them:" -ForegroundColor White
        Write-Host "  - To DISABLE all CC content, type " -ForegroundColor White -NoNewline
        Write-Host "disable" -ForegroundColor Yellow
        Write-Host "  - To RESTORE all disabled CC content, type " -ForegroundColor White -NoNewline
        Write-Host "restore" -ForegroundColor Green
        Write-Host ""
        Write-Host "Supports ranges: 1-5,8,10-12" -ForegroundColor DarkGray
        Write-Host ""
        Write-Host "Page $($currentPage + 1) of $totalPages" -ForegroundColor Cyan
        Write-Host ""
        
        # Display current page
        $startIdx = $currentPage * $pageSize
        $endIdx = [Math]::Min($startIdx + $pageSize, $ccList.Count)
        
        for ($i = $startIdx; $i -lt $endIdx; $i++) {
            $item = $ccList[$i]
            Write-Host "  [$($item.Index)] " -ForegroundColor Yellow -NoNewline
            
            if ($item.IsActive) {
                Write-Host "$($item.FriendlyName)" -ForegroundColor White -NoNewline
                Write-Host " [$($item.BA2Count) BA2s]" -ForegroundColor Cyan -NoNewline
            } else {
                Write-Host "(DISABLED) " -ForegroundColor DarkGray -NoNewline
                Write-Host "$($item.FriendlyName)" -ForegroundColor DarkGray -NoNewline
                Write-Host " [0 BA2s]" -ForegroundColor DarkGray -NoNewline
            }
            
            Write-Host " ($($item.PluginName))" -ForegroundColor DarkGray
        }
        
        Write-Host ""
        Write-Host "----------------------------------------" -ForegroundColor DarkGray
        
        # Navigation options
        if ($totalPages -gt 1) {
            Write-Host "Navigation: " -NoNewline -ForegroundColor White
            Write-Host "n" -NoNewline -ForegroundColor Yellow
            Write-Host "=Next | " -NoNewline -ForegroundColor White
            Write-Host "p" -NoNewline -ForegroundColor Yellow
            Write-Host "=Previous | " -NoNewline -ForegroundColor White
            Write-Host "h" -NoNewline -ForegroundColor Yellow
            Write-Host "=First | " -NoNewline -ForegroundColor White
            Write-Host "e" -NoNewline -ForegroundColor Yellow
            Write-Host "=Last | " -NoNewline -ForegroundColor White
            Write-Host "q" -NoNewline -ForegroundColor Yellow
            Write-Host "=Quit" -ForegroundColor White
        } else {
            Write-Host "Type " -NoNewline -ForegroundColor White
            Write-Host "q" -NoNewline -ForegroundColor Yellow
            Write-Host " to return to main menu" -ForegroundColor White
        }
        Write-Host "Enter your selection or press Enter to cancel" -ForegroundColor White
        Write-Host ""
        
        $userInput = Read-Host "Your choice"
        
        # Handle navigation
        $inputLower = $userInput.Trim().ToLower()
        if ($inputLower -eq 'n' -and $currentPage -lt ($totalPages - 1)) {
            $currentPage++
            continue
        } elseif ($inputLower -eq 'p' -and $currentPage -gt 0) {
            $currentPage--
            continue
        } elseif ($inputLower -eq 'h') {
            $currentPage = 0
            continue
        } elseif ($inputLower -eq 'e') {
            $currentPage = $totalPages - 1
            continue
        } elseif ($inputLower -eq 'q' -or [string]::IsNullOrWhiteSpace($userInput)) {
            return
        } else {
            # Treat as selection
            $selection = $userInput
            break
        }
    }
    
    # Check for special keywords
    $inputLower = $selection.ToLower().Trim()
    
    # Initialize arrays (ensure clean state)
    $itemsToDisable = @()
    $itemsToEnable = @()
    
    if ($inputLower -eq 'disable') {
        # Disable ALL active CC items
        $itemsToDisable = $ccList | Where-Object { $_.IsActive }
        $itemsToEnable = @()
        
        if ($itemsToDisable.Count -eq 0) {
            Write-Host "All CC content is already disabled!" -ForegroundColor Yellow
            Start-Sleep -Seconds 2
            continue
        }
        
        Write-Host ""
        Write-Host "DISABLE ALL CC CONTENT" -ForegroundColor Red
        Write-Host "This will disable all $($itemsToDisable.Count) active CC items (~$($itemsToDisable.Count * 2) BA2 files)" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Ready to disable ALL? Type " -NoNewline
        Write-Host "yes" -ForegroundColor Green -NoNewline
        Write-Host " to continue (any other key to cancel)"
        $confirm = (Read-Host).Trim().ToLower()
        
        if ($confirm -ne 'yes') {
            Write-Host "Cancelled." -ForegroundColor Yellow
            Start-Sleep -Seconds 2
            continue
        }
    }
    elseif ($inputLower -eq 'restore') {
        # Enable ALL disabled CC items
        $itemsToEnable = $ccList | Where-Object { -not $_.IsActive }
        $itemsToDisable = @()
        
        if ($itemsToEnable.Count -eq 0) {
            Write-Host "All CC content is already enabled!" -ForegroundColor Yellow
            Start-Sleep -Seconds 2
            continue
        }
        
        Write-Host ""
        Write-Host "RESTORE ALL CC CONTENT" -ForegroundColor Green
        Write-Host "This will enable all $($itemsToEnable.Count) disabled CC items (~$($itemsToEnable.Count * 2) BA2 files)" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Ready to restore ALL? Type " -NoNewline
        Write-Host "yes" -ForegroundColor Green -NoNewline
        Write-Host " to continue (any other key to cancel)"
        $confirm = (Read-Host).Trim().ToLower()
        
        if ($confirm -ne 'yes') {
            Write-Host "Cancelled." -ForegroundColor Yellow
            Start-Sleep -Seconds 2
            continue
        }
    }
    else {
        # Parse selection (supports ranges like "1-5,8,10-12")
        $selectedIndices = @()
        try {
            $numbers = Parse-NumberRanges -inputString $selection -maxValue $ccList.Count
            foreach ($num in $numbers) {
                $selectedIndices += ($num - 1)  # Convert to 0-based index
            }
        } catch {
            Write-Host "Invalid input! Use format: 1-5,8,10-12" -ForegroundColor Red
            Start-Sleep -Seconds 2
            continue
        }
        
        if ($selectedIndices.Count -eq 0) {
            Write-Host "No valid selections." -ForegroundColor Yellow
            Start-Sleep -Seconds 2
            continue
        }
        
        # Separate active and disabled items
        $itemsToDisable = @()
        $itemsToEnable = @()
        
        foreach ($idx in $selectedIndices) {
            $item = $ccList[$idx]
            if ($item.IsActive) {
                $itemsToDisable += $item
            } else {
                $itemsToEnable += $item
            }
        }
        
        # Show what will happen
        Write-Host ""
        if ($itemsToDisable.Count -gt 0) {
            Write-Host "Items to DISABLE ($($itemsToDisable.Count)):" -ForegroundColor Red
            foreach ($item in $itemsToDisable) {
                Write-Host "  - $($item.FriendlyName)" -ForegroundColor White
            }
            Write-Host ""
        }
        
        if ($itemsToEnable.Count -gt 0) {
            Write-Host "Items to ENABLE ($($itemsToEnable.Count)):" -ForegroundColor Green
            foreach ($item in $itemsToEnable) {
                Write-Host "  - $($item.FriendlyName)" -ForegroundColor DarkGray
            }
            Write-Host ""
        }
    }
    
    Write-Host ""
    Write-Host "Modifying Creation Club content..." -ForegroundColor Yellow
    
    # Read Fallout4.ccc
    $cccContent = Get-Content $cccPath
    $newCccContent = @()
    $disabledCount = 0
    $enabledCount = 0
    
    # Build list of plugins to disable
    $disablePlugins = @()
    foreach ($item in $itemsToDisable) {
        $disablePlugins += $item.PluginName
    }
    
    # Filter out disabled CC items from .ccc file
    foreach ($line in $cccContent) {
        $shouldDisable = $false
        $trimmedLine = $line.Trim()
        foreach ($plugin in $disablePlugins) {
            if ($trimmedLine -ieq $plugin) {
                $shouldDisable = $true
                $disabledCount++
                Write-Host "  Disabled: $plugin" -ForegroundColor Red
                break
            }
        }
        
        if (-not $shouldDisable) {
            $newCccContent += $line
        }
    }
    
    # Add enabled CC items to .ccc file (append-only, avoid duplicates)
    foreach ($item in $itemsToEnable) {
        $plugin = $item.PluginName
        if (-not ($newCccContent | ForEach-Object { $_.Trim() } | Where-Object { $_ -ieq $plugin })) {
            $newCccContent += $plugin
            $enabledCount++
            Write-Host "  Enabled: $plugin" -ForegroundColor Green
        }
    }
    
    # Calculate BA2 changes
    $ba2Reduction = 0
    $ba2Increase = 0
    
    foreach ($item in $itemsToDisable) {
        if ($item.BA2Count) {
            $ba2Reduction += $item.BA2Count
        }
    }
    
    foreach ($item in $itemsToEnable) {
        if ($item.BA2Count) {
            $ba2Increase += $item.BA2Count
        }
    }
    
    $netBA2Change = $ba2Increase - $ba2Reduction
    
    # Backup original Fallout4.ccc
    $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
    $backupPath = "$cccPath.backup_$timestamp"
    Copy-Item $cccPath $backupPath -Force
    Write-Host ""
    Write-Host "Backup created: Fallout4.ccc.backup_$timestamp" -ForegroundColor Cyan
    
    # Write modified Fallout4.ccc
    $newCccContent | Set-Content $cccPath -Encoding ASCII
    
    Write-Host ""
    Write-Host "SUCCESS!" -ForegroundColor Green
    if ($disabledCount -gt 0) {
        Write-Host "Disabled $disabledCount CC plugin(s)" -ForegroundColor White
    }
    if ($enabledCount -gt 0) {
        Write-Host "Enabled $enabledCount CC plugin(s)" -ForegroundColor White
    }
    
    if ($netBA2Change -lt 0) {
        Write-Host "Your BA2 count will decrease by $([Math]::Abs($netBA2Change)) files" -ForegroundColor Cyan
    } elseif ($netBA2Change -gt 0) {
        Write-Host "Your BA2 count will increase by $netBA2Change files" -ForegroundColor Yellow
    } else {
        Write-Host "Your BA2 count will remain the same" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "IMPORTANT: Changes will take effect next time you launch Fallout 4!" -ForegroundColor Yellow
    Write-Log "CC_MODIFIED|Disabled:$disabledCount|Enabled:$enabledCount|BA2Change:$netBA2Change|$(Get-Date)"
    
    Write-Host ""
    $response = (Read-Host "Press Enter to return to your page, or type 'q' to return to main menu").Trim().ToLower()
    if ($response -eq 'q') {
        return
    }
    
    # Re-scan CC content to update states, but stay on current page
    # This continues the outer function loop which rebuilds the CC list
    # but we preserve $currentPage so user returns to their page
    continue  # Continue outer loop to rebuild CC list
    }
}# ============================================

# ============================================
# Main Menu
# ============================================
function Show-Menu {
    Show-Header
    
    Write-Host "IF YOU DON'T KNOW HOW TO SAFELY DEAL WITH BA2 ARCHIVES AND LOOSE FILES" -ForegroundColor Red
    Write-Host "YOU SHOULD CLOSE THIS FILE AND USE THE STANDARD VERSION." -ForegroundColor Red
    Write-Host ""
    Write-Host "DISCLAIMER:" -ForegroundColor Yellow
    Write-Host "This software is provided AS-IS with no guarantees or warranties of any kind." -ForegroundColor Gray
    Write-Host "The author is not liable for any damage to your Fallout 4 installation," -ForegroundColor Gray
    Write-Host "operating system, hardware, or any other consequences resulting from its use," -ForegroundColor Gray
    Write-Host "up to and including loss of life and/or destruction of immortal souls." -ForegroundColor Gray
    Write-Host "Use at your own risk. Always backup your data before making changes." -ForegroundColor Gray
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor DarkGray
    Write-Host ""
    
    Write-Host "1" -ForegroundColor Yellow -NoNewline
    Write-Host ". Show Current Total BA2 Count"
    Write-Host "2" -ForegroundColor Yellow -NoNewline
    Write-Host ". Manage BA2 Mods (Extract/Restore)"
    Write-Host "3" -ForegroundColor Yellow -NoNewline
    Write-Host ". Manage Creation Club Content (Enable/Disable)"
    Write-Host "4" -ForegroundColor Yellow -NoNewline
    Write-Host ". View Extraction Log"
    Write-Host "5" -ForegroundColor Yellow -NoNewline
    Write-Host ". Exit"
    Write-Host ""
    Write-Host "Select an option (" -NoNewline
    Write-Host "1-5" -ForegroundColor Yellow -NoNewline
    Write-Host "): " -NoNewline
    $choice = Read-Host
    return $choice
}

# ============================================
# Main Loop
# ============================================
while ($true) {
    $choice = Show-Menu

    switch ($choice) {
        "1" { Count-BA2Files }
        "2" { Manage-BA2Mods }
        "3" { Manage-CreationClub }
        "4" { View-Log }
        "5" { 
            Write-Host ""
            Write-Host "Thank you for using Manage BA2!" -ForegroundColor Green
            Start-Sleep -Seconds 2
            exit 0
        }
        default {
            Write-Host ""
            Write-Host "Invalid choice. Please try again." -ForegroundColor Red
            Start-Sleep -Seconds 2
        }
    }
}
