# Renzo-Prisoner Cart Collision Fix

Mesh-only overlay for Skyrim SE (Immersive 2026 / 1.7.104). Stops the
Helgen opening cart from bouncing by applying the collision-flag edit
from [Prisoner Cart Opening Fix SE and AE](https://www.nexusmods.com/skyrimspecialedition/mods/60968)
(Nexus 60968) to the **currently winning** cart mesh, instead of
replacing that mesh with 60968's vanilla, SMIM 2.08, or RCI 3.2a nif.

Author: Renzo

## Credit

The flag values and the two fields they belong to come from Nexus 60968,
"Prisoner Cart Opening Fix SE and AE," by dannyhand. That mod documents:

> BSFadeNode > bhkCollisionObject > bhkRigidBody : Flags and Part Numbers = 224
> BSFadeNode > bhkCollisionObject > bhkRigidBody : Havok Filter Copy > Flags and Part Numbers = 224

224 decimal is `0b11100000`, which turns off collision for the cart.

## What was confirmed

Official 60968 archives were diffed against their sources:

| Pair | Result |
|---|---|
| SMIM 2.08 vs 60968 SMIM 2.08 Patch 1.1 (file 252759) | Same file size (847009). The only *block data* change is the two flag bytes below. NifSkope also reordered the type-name list (`BSTriShape` vs `BSLightingShaderProperty`), which shows up as header/type-index diffs and is not part of the fix. |
| RCI 3.2c vs 60968 RCI 3.2a Patch 1.2 (file 252968) | Same two payload bytes, same incidental type-list reorder. |

In both pairs, on the root cart `bhkRigidBody` (the body referenced by
`BSFadeNode` → `bhkCollisionObject`):

- Havok Filter, byte "Flags and Part Numbers" (block +5): `0` → `224`
- Havok Filter Copy, byte "Flags and Part Numbers" (block +37): `0` → `224`

The packed `HavokFilter` uint32 at block +4 and +36 changes from
`0x0000000A` (layer 10, flags 0) to `0x0000E00A` (layer 10, flags 224).
No other rigid bodies (wheels, etc.) are touched.

## This file

A copy of `Renzo-PG Patcher Output`'s
`meshes/furniture/prisonercarriage/prisonercarriage01.nif` with **only**
those two bytes changed. No ESP. Load after PG Patcher Output.

| File | md5 | size |
|---|---|---:|
| PG Patcher source | `9ae2ab2340ef63c1460fc29e2cc57461` | 826756 |
| This overlay | `3434539ae7c9ed15699471954c7728b5` | 826756 |
| Differing bytes | file+4710 and file+4742 (`0`→`224`) | 2 |

## Plugin

None. Loose mesh only.

Deploy only when SkyrimSE.exe is not running. Hair Facegen stays last in
order.json.
