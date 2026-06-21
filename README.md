# Universal Tactical Light Framework

Generic scripted tactical light framework for S.T.A.L.K.E.R. Anomaly / GAMMA weapon mods.

## Requirements

- Anomaly/GAMMA with Modded Exes support for `attachment_script_light`.
- At least one weapon compatibility patch that registers supported weapon sections.
- MCM is optional, but required to change the default keybind.

## Installation

Enable `Universal Tactical Light Framework` before any UTLF weapon compatibility patch in MO2 so patch scripts can call the framework during startup. This framework provides the runtime and default tactical light items; compatibility patches provide the weapon registrations and profile data.

## Controls

- Press the UTLF toggle key combo to toggle the scripted weapon tactical light.
- The default combo is `Alt + L`.
- The key and modifier can be changed in MCM under `Universal Tactical Light Framework` > `Framework`.
- The input handler consumes the configured combo press/release and suppresses the vanilla torch helper for that input, so `Alt + L` should not toggle the vanilla headlamp while UTLF is active.

## Modular Tactical Light Item

UTLF provides real inventory addon items:

- Rifle/long-gun lights in `utlf_rifles`: `utlf_tactical_light` (M600DF) and `utlf_tactical_light_m300c` (M300C).
- Pistol lights in `utlf_pistols`: `utlf_tactical_light_x300`, `utlf_tactical_light_foxtrot1`, `utlf_tactical_light_olight`, and `utlf_tactical_light_streamlight`.
- `base` is retained as a legacy alias for the rifle/long-gun group only.

These runtime defaults are registered by `utlf_registry.script`. The item config also mirrors the group names under `[utlf_tactical_light_groups]` for reference.

Current modular flashlight item profiles:

| Section | Light | Cost | Weight | Range | Cone | Texture | Color |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `utlf_tactical_light_foxtrot1` | FOXTROT1X | `14000` | `0.068` | `38` | `38` | `utlf\lights\spot_throw` | `0.98,0.97,0.94,0.55` |
| `utlf_tactical_light_olight` | BALDR Pro | `23000` | `0.129` | `43` | `58` | `utlf\lights\spot_flood` | `1.00,0.96,0.86,0.55` |
| `utlf_tactical_light_streamlight` | TLR-1 HL | `24000` | `0.123` | `51` | `42` | `utlf\lights\spot_throw` | `0.97,0.96,0.94,0.55` |
| `utlf_tactical_light_x300` | X300U-B | `30000` | `0.116` | `38` | `60` | `utlf\lights\spot_flood` | `1.00,0.98,0.95,0.55` |
| `utlf_tactical_light_m300c` | M300C | `19000` | `0.116` | `32` | `50` | `utlf\lights\spot_balanced` | `1.00,0.95,0.86,0.55` |
| `utlf_tactical_light` | M600DF | `36000` | `0.156` | `45` | `62` | `utlf\lights\spot_flood` | `1.00,0.99,0.95,0.55` |

For modular weapon profiles, drag one of these items onto a supported weapon in the inventory. UTLF stores the attached item on that specific weapon, adds an inventory icon layer, creates a visible scripted attachment model when the weapon is drawn, and returns the item when detached through the inventory context menu.

## Optional Integrations

Drag/drop attachment is the primary modular attach path. When `rax_icon_layers` is available, UTLF registers an icon overlay for weapons with a saved modular flashlight. When `custom_functor_autoinject` is available, UTLF adds an inventory context action to detach the saved modular flashlight and return the item.

## MCM Pages

Compatibility patches can add their own pages under the shared `Universal Tactical Light Framework` MCM entry by returning their MCM page with the collection name `"utlf"`:

```lua
function on_mcm_load()
    return {
        id = "my_weapon_pack",
        sh = true,
        gr = {
            { id = "range", type = "track", val = 2, min = 5, max = 80, step = 1, def = 26 },
            { id = "cone_deg", type = "track", val = 2, min = 8, max = 60, step = 1, def = 24 },
        },
    }, "utlf"
end
```

Patch scripts can read numeric MCM values through the framework helper:

```lua
local range = utlf.get_mcm_number("utlf/my_weapon_pack/range", 26, 5, 80)
local cone_deg = utlf.get_mcm_number("utlf/my_weapon_pack/cone_deg", 24, 8, 60)
```

`get_mcm_number(path, fallback, min, max)` returns the fallback when MCM is unavailable or the stored value is invalid, and clamps valid values to the provided bounds.

For configurable built-in light profiles, prefer `setup_builtin_light_pack()` so the framework handles MCM reads, profile registration, option-change refresh, and active-light rebuilds:

```lua
local PACK_NAME = "My Weapon Pack"

local PROFILE = {
    sections = { "wpn_my_weapon", "wpn_my_weapon_alt" },
    mode = "built_in",
}

local CONFIG = {
    page = "my_weapon_pack",
    numbers = {
        range = { def = 26, min = 5, max = 80 },
        cone_deg = { def = 24, min = 8, max = 60 },
    },
}

function on_game_start()
    if utlf and utlf.setup_builtin_light_pack then
        utlf.setup_builtin_light_pack(PACK_NAME, PROFILE, CONFIG)
    else
        printf("[utlf_my_weapon] compatible framework script not available")
    end
end
```

`CONFIG.page` is the MCM namespace for that weapon patch. Use a unique value per compatibility patch so each built-in weapon pack stores its own `range`, `cone_deg`, and future options independently. Modular flashlight emitter values belong on the flashlight item section instead, not on the weapon patch profile.

## Public API

Compatibility patches should call the small facade in `utlf.script` instead of internal modules:

| Function | Use |
| --- | --- |
| `register_pack(pack_name, profiles)` | Register one or more tested weapon profiles from a patch. |
| `register_light(section, profile)` | Register a single weapon section/profile pair when a pack table is unnecessary. |
| `register_attachment_group(group_name, sections)` | Add reusable modular flashlight groups for patch-specific item allow-lists. |
| `setup_builtin_light_pack(pack_name, profile, config)` | Register a configurable built-in light profile and rebuild the active light after MCM changes. |
| `clamp_number(value, fallback, min, max)` | Clamp numeric configuration values when a patch reads its own non-MCM source. |
| `get_mcm_number(path, fallback, min, max)` | Read and clamp optional numeric MCM values with a fallback when MCM is unavailable. |
| `get_default_toggle_key()` | Read the framework default toggle key for UI/config integration. |
| `get_default_toggle_modifier()` | Read the framework default toggle modifier for UI/config integration. |
| `rebuild_active_light(reason)` | Recreate the currently active scripted light after a patch changes profile data or settings. |
| `on_option_change()` | Framework option-change callback; patches normally use `setup_builtin_light_pack()` instead of calling this directly. |

Parser helpers are internal and are not part of the compatibility-patch API.

## Profile Fields

Common fields:

- `sections`: weapon section names supported by this profile.
- `mode`: `built_in` or `modular`. Defaults to `built_in`.
- `reattach_delay_ms`: delay after object replacement. Defaults to `250`.
- `replacement_window_ms`: maximum time after a known replacement where reattaching is allowed. Defaults to `1000`.

Built-in-only fields:

- `fire_bone`: HUD bone used as the invisible carrier attachment parent. Defaults to the weapon HUD `fire_bone` or `wpn_body`.
- `fire_point`: local attachment offset. Defaults to `0,0,0.035`.
- `model`: optional invisible carrier model. Defaults to the weapon `visual` without `.ogf`.
- `attachment_scale`: invisible carrier model scale. Defaults to `0.001`.
- `shadow`: enables dynamic shadows. Defaults to `true`; set `false` to opt out.
- `hud_mode`: uses the HUD lighting path when set to `true`. Defaults to `false`.
- `light_bone`: bone the script light attaches to. Defaults to `wpn_body`.
- `range`: light range. Defaults to `26`.
- `cone_deg`: spot cone angle in degrees. Defaults to `24`.
- `color`: `{ r, g, b, a }`. Defaults to warm white.
- `texture`: light texture. Defaults to `internal\internal_tactical_torch`.

Modular-only fields:

- `allowed_attachments`: allowed UTLF item sections. Use this for weapon-specific exceptions.
- `attachment_groups`: allowed framework attachment groups. Handgun profiles should use `{ "utlf_pistols" }`; rifles, SMGs/PDWs, shotguns, and other long guns should use `{ "utlf_rifles" }`. Defaults to `{ "base" }`, which is retained as a rifle-compatible legacy alias.
- `mount`: weapon mount anchor for the common one-mount case. Modular profiles must define `mount` or `mounts`.
- `mount.class`: mount compatibility class, such as `rifle_side` or `pistol_underbarrel`.
- `mount.position`: `{ x, y, z }` root mount local position. Defaults to `{ 0, 0, 0 }`.
- `mount.rotation`: `{ x, y, z }` root mount local rotation. Defaults to `{ 0, 0, 0 }`.
- `mount.scale`: root mount scale. Defaults to `1`.
- `mount.bone`: root mount parent bone. Defaults to `0`.
- `mount.light_direction`: optional mount-aware beam direction as `{ x, y, z }` in degrees, matching the other rotation fields. Runtime converts these values to radians for `attachment_script_light:set_direction()`. Use this when the same flashlight item needs different beam correction on different weapon mount orientations.
- `mount.adapters`: optional per-item adapter overrides keyed by item section.
- `mount.adapters[section].light_direction`: optional item-specific beam direction override for one flashlight on this mount. `mount.adapters.default.light_direction` can provide a default override for all items on the mount.
- `mounts`: optional future multi-mount table. UTLF picks the first mount whose `class` matches the selected flashlight item's `mount_class`.

Modular attachments use nested script attachments. The weapon receives a hidden root mount carrier at the weapon-defined anchor, then the selected flashlight model is attached as a child using the item adapter transform. Weapon patches define mount anchors; flashlight items define model-specific offsets and beam direction.

For modular lights, runtime beam direction is resolved in this order: `mount.adapters[item_section].light_direction`, `mount.adapters.default.light_direction`, `mount.light_direction`, then the flashlight item's own `light_direction`. Built-in weapon lights do not use this modular mount resolver.

Modular tactical light item fields:

- `scripted_model`: visible model attached as the child flashlight.
- `mount_class`: item compatibility class. It must match a weapon mount class.
- `adapter_position`: item model offset from the root mount as `x,y,z`.
- `adapter_rotation`: item model rotation from the root mount as `x,y,z`.
- `adapter_scale`: item model scale from the root mount.
- `adapter_bone`: root mount carrier bone used as the item adapter parent. Defaults to `0`.
- `light_bone`: bone inside the scripted model used as the light emitter origin.
- `light_direction`: item-specific beam direction as `x,y,z` in degrees. Runtime converts these values to radians for `attachment_script_light:set_direction()`. Defaults to `0,0,0`.
- `light_range`: item-specific light range.
- `light_cone_deg`: item-specific spot cone angle in degrees.
- `light_texture`: item-specific light texture.
- `light_color`: item-specific color as `r,g,b,a`.
- `light_type`: item-specific light type. Defaults to spot light.
- `light_shadow`: item-specific dynamic shadow toggle.
- `light_hud_mode`: item-specific HUD lighting path toggle.
- `light_volumetric`, `light_volumetric_distance`, `light_volumetric_intensity`, `light_volumetric_quality`: item-specific volumetric settings.

Each modular flashlight item defines its own model and emitter settings. Weapon patches define which flashlight items are allowed, where they are mounted, and any mount-specific beam direction correction; modular weapon profiles do not control `range`, `cone_deg`, `texture`, `color`, `light_bone`, or other emitter behavior.

Weapon patches can define additional attachment groups through:

```lua
utlf.register_attachment_group("my_pack_lights", { "utlf_tactical_light" })
```

Example handgun profile:

```lua
{ sections = { "wpn_my_pistol" }, mode = "modular", attachment_groups = { "utlf_pistols" }, mount = { class = "pistol_underbarrel", position = { 0, 0, 0 }, rotation = { 0, 0, 0 }, scale = 1, bone = 0, light_direction = { 0, 0, 0 } } }
```

Example long-gun profile:

```lua
{ sections = { "wpn_my_rifle" }, mode = "modular", attachment_groups = { "utlf_rifles" }, mount = { class = "rifle_side", position = { 0, 0, 0 }, rotation = { 0, 0, 0 }, scale = 1, bone = 0, light_direction = { 0, 0, 0 } } }
```

## Shadows And HUD Mode

The framework defaults to `shadow = true` and `hud_mode = false`. This makes the light follow the weapon attachment while using the normal world-lighting path, which is more stable for shadowed weapon lights.

`hud_mode = true` can change lighting and shadow behavior. Use it only if a specific built-in profile or modular flashlight item has been tested with it.

If a built-in weapon profile or modular flashlight item flickers or is too expensive with shadows enabled, set its shadow option to `false`.

## Maintainer Checks

Run the deterministic beam asset check before release:

```sh
python3 tools/generate_utlf_light_profiles.py --check
```

The release workflow creates `Universal_Tactical_Light_Framework-<version>.zip` from `gamedata/`, `README.md`, and `meta.ini`, then stamps `meta.ini` with the tag-derived version and archive name. Generated PNG previews and the contact sheet under `tools/light_profile_previews/` stay outside release archives.

## Notes For Weapon Authors

Register only weapons you have tested. Automatic detection is intentionally not used because weapon HUD bones, decorative lights, and replacement sections vary too much between mods.

Use `mode = "modular"` for weapons where the player should attach/detach a flashlight item. Use `mode = "built_in"` for weapons that already have a fixed integrated flashlight model or where external flashlight modules should not be allowed.

Tactical light state is not transferred across normal weapon switches. The framework only reattaches automatically during a known 3DSS magnifier replacement, where the old weapon object is intentionally swapped for another registered section.

UTLF avoids `actor_on_update`. Modular attachments are created on HUD draw animations, inventory drag/drop attaches the saved item state, and known 3DSS replacement repair uses one-shot time events.

## Internal Script Layout

- `utlf.script`: small public facade used by compatibility patches.
- `utlf_parse.script`: internal parsing helpers for strings, INI values, vectors, colors, and bones.
- `utlf_core.script`: shared defaults, MCM value helpers, common weapon/model helpers, and compatibility facade for internal modules.
- `utlf_state.script`: runtime state, MCM key settings, active weapon object lookup, and replacement-window flags.
- `utlf_profile.script`: profile copying, section normalization, profile normalization, mount parsing/resolution, allowed attachment checks, and vector/color helpers.
- `utlf_registry.script`: registered weapon profiles, attachment groups, profile lookup, and active supported weapon lookup.
- `utlf_items.script`: modular flashlight item config, saved modular item state, item light profiles, and modular model lookup.
- `utlf_lights.script`: scripted light lifecycle, built-in carrier attachments, rebuilds, and save cleanup.
- `utlf_replacement.script`: 3DSS magnifier replacement wrapping, delayed light transfer, and HUD draw replacement repair.
- `utlf_input.script`: toggle key handling, vanilla torch suppression, modifier checks, and click sound playback.
- `utlf_modular.script`: nested modular mount and visible tactical light attachment creation/removal.
- `utlf_inventory.script`: inventory drag/drop, attachment highlighting, icon layer, and detach context action.
- `utlf_mcm.script`: framework MCM page registration.
