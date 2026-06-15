# Universal Tactical Light Framework

Generic scripted tactical light framework for S.T.A.L.K.E.R. Anomaly / GAMMA weapon mods.

## Requirements

- Anomaly/GAMMA with Modded Exes support for `attachment_script_light`.
- At least one weapon compatibility patch that registers supported weapon sections.
- MCM is optional, but required to change the default keybind.

## Controls

- Press the UTLF toggle key combo to toggle the scripted weapon tactical light.
- The default combo is `Alt + L`.
- The key and modifier can be changed in MCM under `Universal Tactical Light Framework` > `Framework`.
- The input handler consumes the configured combo press/release and suppresses the vanilla torch helper for that input, so `Alt + L` should not toggle the vanilla headlamp while UTLF is active.

## Modular Tactical Light Item

UTLF provides a real inventory addon item:

- `utlf_tactical_light`: Tactical Light Module

For modular weapon profiles, drag this item onto a supported weapon in the inventory. UTLF stores the attached item on that specific weapon, adds an inventory icon layer, creates a visible scripted attachment model when the weapon is drawn, and returns the item when detached through the inventory context menu.

The current item uses a temporary PEQ/laser mesh and icon placeholder.
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

For configurable built-in light profiles, prefer `setup_configured_pack()` so the framework handles MCM reads, profile registration, option-change refresh, and active-light rebuilds:

```lua
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
    if utlf and utlf.setup_configured_pack then
        utlf.setup_configured_pack(PACK_NAME, PROFILE, CONFIG)
    else
        printf("[utlf_my_weapon] compatible framework script not available")
    end
end
```

`CONFIG.page` is the MCM namespace for that weapon patch. Use a unique value per compatibility patch so each built-in weapon pack stores its own `range`, `cone_deg`, and future options independently. Modular flashlight emitter values belong on the flashlight item section instead, not on the weapon patch profile.


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

- `allowed_attachments`: allowed UTLF item sections. Defaults to the framework `base` group, currently `utlf_tactical_light`.
- `attachment_groups`: allowed framework attachment groups. Defaults to `{ "base" }`.
- `transform`: visible attachment transform table.
- `transform.position`: `{ x, y, z }` visible attachment local position. Defaults to `{ 0, 0, 0 }`.
- `transform.rotation`: `{ x, y, z }` visible attachment local rotation. Defaults to `{ 0, 0, 0 }`.
- `transform.scale`: visible attachment scale. Defaults to `1`.
- `transform.bone`: visible attachment parent bone. Defaults to `0`.

Modular tactical light item fields:

- `scripted_model`: visible model attached to the weapon.
- `light_bone`: bone inside the scripted model used as the light emitter origin.
- `light_range`: item-specific light range.
- `light_cone_deg`: item-specific spot cone angle in degrees.
- `light_texture`: item-specific light texture.
- `light_color`: item-specific color as `r,g,b,a`.
- `light_type`: item-specific light type. Defaults to spot light.
- `light_shadow`: item-specific dynamic shadow toggle.
- `light_hud_mode`: item-specific HUD lighting path toggle.
- `light_volumetric`, `light_volumetric_distance`, `light_volumetric_intensity`, `light_volumetric_quality`: item-specific volumetric settings.

Each modular flashlight item defines its own model and emitter settings. Weapon patches only define which flashlight items are allowed and where they are mounted; modular weapon profiles do not control `range`, `cone_deg`, `texture`, `color`, `light_bone`, or other emitter behavior.

Weapon patches can define additional attachment groups through:

```lua
utlf.register_attachment_group("my_pack_lights", { "utlf_tactical_light" })
```

## Shadows And HUD Mode

The framework defaults to `shadow = true` and `hud_mode = false`. This makes the light follow the weapon attachment while using the normal world-lighting path, which is more stable for shadowed weapon lights.

`hud_mode = true` can change lighting and shadow behavior. Use it only if a specific built-in profile or modular flashlight item has been tested with it.

If a built-in weapon profile or modular flashlight item flickers or is too expensive with shadows enabled, set its shadow option to `false`.

## Notes For Weapon Authors

Register only weapons you have tested. Automatic detection is intentionally not used because weapon HUD bones, decorative lights, and replacement sections vary too much between mods.

Use `mode = "modular"` for weapons where the player should attach/detach a flashlight item. Use `mode = "built_in"` for weapons that already have a fixed integrated flashlight model or where external flashlight modules should not be allowed.

Tactical light state is not transferred across normal weapon switches. The framework only reattaches automatically during a known 3DSS magnifier replacement, where the old weapon object is intentionally swapped for another registered section.

UTLF avoids `actor_on_update`. Modular attachments are created on HUD draw animations, inventory drag/drop attaches the saved item state, and known 3DSS replacement repair uses one-shot time events.

## Internal Script Layout

- `utlf.script`: small public facade used by compatibility patches.
- `utlf_core.script`: shared defaults, state, profile registration, MCM value helpers, weapon/profile lookup, and saved modular item data.
- `utlf_lights.script`: scripted light lifecycle, built-in carrier attachments, HUD draw repair, save cleanup, and 3DSS magnifier replacement repair.
- `utlf_input.script`: toggle key handling, vanilla torch suppression, modifier checks, and click sound playback.
- `utlf_modular.script`: visible modular tactical light attachment creation/removal.
- `utlf_inventory.script`: inventory drag/drop, attachment highlighting, icon layer, and detach context action.
- `utlf_mcm.script`: framework MCM page registration.
