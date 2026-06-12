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
- `shadow`: enables dynamic shadows. Defaults to `true`; set `false` to opt out.
- `hud_mode`: uses the HUD lighting path when set to `true`. Defaults to `false`.
- `fire_bone`: HUD bone used as the carrier attachment parent. Defaults to the weapon HUD `fire_bone` or `wpn_body`.
- `fire_point`: local attachment offset. Defaults to `0,0,0.035`.
- `light_bone`: bone the script light attaches to. Defaults to `wpn_body`.
- `attachment_model` or `model`: optional carrier model. Defaults to the weapon `visual` without `.ogf`.
- `attachment_scale`: carrier model scale. Defaults to `0.001`.
- `range`: light range. Defaults to `26`.
- `cone_deg`: spot cone angle in degrees. Defaults to `24`.
- `color`: `{ r, g, b, a }`. Defaults to warm white.
- `texture`: light texture. Defaults to `internal\internal_tactical_torch`.
- `reattach_delay_ms`: delay after object replacement. Defaults to `250`.
- `pre_replacement_delay_ms`: delay after known magnifier replacement. Defaults to `400`.
- `replacement_window_ms`: maximum time after a known replacement where reattaching is allowed. Defaults to `1000`.

## Shadows And HUD Mode

The framework defaults to `shadow = true` and `hud_mode = false`. This makes the light follow the weapon attachment while using the normal world-lighting path, which is more stable for shadowed weapon lights.

`hud_mode = true` can change lighting and shadow behavior. Use it only if a specific weapon profile has been tested with it.

If a weapon profile flickers or is too expensive with shadows enabled, set `shadow = false` in that profile.

## Notes For Weapon Authors

Register only weapons you have tested. Automatic detection is intentionally not used because weapon HUD bones, decorative lights, and replacement sections vary too much between mods.

Tactical light state is not transferred across normal weapon switches. The framework only reattaches automatically during a known 3DSS magnifier replacement, where the old weapon object is intentionally swapped for another registered section.
