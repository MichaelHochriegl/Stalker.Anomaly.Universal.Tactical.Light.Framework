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

The current item uses a temporary PEQ/laser mesh and icon placeholder. Replace those assets with real flashlight assets before publishing if you do not have redistribution permission for the placeholder files.

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

For common configurable light profiles, prefer `setup_configured_pack()` so the framework handles MCM reads, profile registration, option-change refresh, and active-light rebuilds:

```lua
local PROFILE = {
    sections = { "wpn_my_weapon", "wpn_my_weapon_alt" },
    attachment_mode = "modular",
    attachment_pos = "0,0,0",
    attachment_rot = "0,0,0",
    attachment_scale = 1,
    attach_bone = 0,
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

`CONFIG.page` is the MCM namespace for that weapon patch. Use a unique value per compatibility patch so each weapon pack stores its own `range`, `cone_deg`, and future options independently.


## Profile Fields

Common fields:

- `sections`: weapon section names supported by this profile.
- `attachment_mode`: `built_in` or `modular`. Defaults to `built_in` for backward compatibility.
- `modular_blacklist`: when `true`, forces `built_in` mode even if another field tries to enable modular attachments.
- `shadow`: enables dynamic shadows. Defaults to `true`; set `false` to opt out.
- `hud_mode`: uses the HUD lighting path when set to `true`. Defaults to `false`.
- `light_bone`: bone the script light attaches to. Defaults to `wpn_body`.
- `range`: light range. Defaults to `26`.
- `cone_deg`: spot cone angle in degrees. Defaults to `24`.
- `color`: `{ r, g, b, a }`. Defaults to warm white.
- `texture`: light texture. Defaults to `internal\internal_tactical_torch`.
- `reattach_delay_ms`: delay after object replacement. Defaults to `250`.
- `pre_replacement_delay_ms`: delay after known magnifier replacement. Defaults to `400`.
- `replacement_window_ms`: maximum time after a known replacement where reattaching is allowed. Defaults to `1000`.

Built-in-only fields:

- `fire_bone`: HUD bone used as the invisible carrier attachment parent. Defaults to the weapon HUD `fire_bone` or `wpn_body`.
- `fire_point`: local attachment offset. Defaults to `0,0,0.035`.
- `attachment_model` or `model`: optional invisible carrier model. Defaults to the weapon `visual` without `.ogf`.
- `attachment_scale`: invisible carrier model scale. Defaults to `0.001`.

Modular-only fields:

- `attachments`: allowed UTLF item sections. Defaults to the framework `base` group, currently `utlf_tactical_light`.
- `attachment_groups`: allowed framework attachment groups. Defaults to `{ "base" }`.
- `attachment_pos` or `attachment_pos_x/y/z`: visible attachment local position.
- `attachment_rot` or `attachment_rot_x/y/z`: visible attachment local rotation.
- `attachment_scale`: visible attachment scale. Defaults to `1`.
- `attach_bone`, `attachment_bone`, or `sl_attach_bone`: visible attachment parent bone. Defaults to `0`.

Weapon patches can define additional attachment groups through:

```lua
utlf.register_attachment_group("my_pack_lights", { "utlf_tactical_light" })
```

## Shadows And HUD Mode

The framework defaults to `shadow = true` and `hud_mode = false`. This makes the light follow the weapon attachment while using the normal world-lighting path, which is more stable for shadowed weapon lights.

`hud_mode = true` can change lighting and shadow behavior. Use it only if a specific weapon profile has been tested with it.

If a weapon profile flickers or is too expensive with shadows enabled, set `shadow = false` in that profile.

## Notes For Weapon Authors

Register only weapons you have tested. Automatic detection is intentionally not used because weapon HUD bones, decorative lights, and replacement sections vary too much between mods.

Use `attachment_mode = "modular"` for weapons where the player should attach/detach a flashlight item. Use `attachment_mode = "built_in"` plus `modular_blacklist = true` for weapons that already have a fixed integrated flashlight model or where external flashlight modules should not be allowed.

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
