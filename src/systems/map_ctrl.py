"""MapController system — owns the open-world map state + the map-management
methods (load_map / transition / teleport_to / discover_neighbors) extracted
from WorldScene (Task 14, Phase 4 ECS restructure).

The controller holds a ref to the WorldScene (self.scene) and reads/writes
scene-level state through it (party, enemies, game, player, world, the ECS
entity adapter, message, floats, camera, chests, ...). Controller-owned state
(the current grid cell c/r, the gen_map dict, the MapRenderer, the village /
landmark caches, the rift secret) lives on self.

The method bodies are copied VERBATIM from WorldScene's _load_map /
_transition / teleport_to / _discover_neighbors; only the `self.X` references
to scene-level state are rewired to `self.scene.X`. Controller-owned state
(self.c / self.r / self._map_data / self.map_renderer / self._village /
self._landmark / self._rift_*) keeps `self.X`. Zero logic lines change.
"""
import random

import src.audio as audio
import src.world.data as WD
from src.data.enemies import ENEMIES_DB
from src.data.heroes import _get_champion_enemy_pool
from src.data.progression import LANDMARK_LORE
from src.data.story import NPCS, STORY_BIOME_QUEST
from src.data.tuning import ENERGY_START
from src.entities import FloatText, WorldEnemy
from src.entities.enemy import spawn_enemy
from src.world.map_renderer import MapRenderer


class MapController:
    """Owns the map grid state + the map-management methods. Constructed by
    WorldScene.__init__ BEFORE _load_map is first called; WorldScene keeps
    settable delegate properties (c / r / _map_data / map_renderer / _village
    / _landmark / _rift_*) that read+write through to the controller so the
    rest of WorldScene's legacy methods keep working unchanged."""

    def __init__(self, scene):
        self.scene = scene
        p = scene.game.player
        # ensure a valid current cell
        if not p.ow_current:
            p.ow_current = [0, 0]
        self.c, self.r = p.ow_current[0], p.ow_current[1]
        # ensure discovered
        if WD.cell_id(self.c, self.r) not in p.ow_discovered:
            p.ow_discovered.append(WD.cell_id(self.c, self.r))
        self.map_renderer = MapRenderer()
        # controller-owned map state (set by load_map on the first call +
        # re-set on every map enter). Declared here so the first load_map
        # doesn't AttributeError on a fresh controller.
        self._map_data = None
        self._village = None
        self._landmark = None
        self._rift_active = False
        self._rift_done = False
        self._rift_enemies = []     # list of WorldEnemy the rift spawned
        self._rift_secret = None    # (x, y, wave_level, wave_size) or None

    @property
    def cell(self):
        """The current grid cell as a (c, r) tuple (the brief's test reads
        mc.cell)."""
        return (self.c, self.r)

    # -----------------------------------------------------------------
    # Map loading + transitions (bodies copied verbatim from WorldScene;
    # self.X -> self.scene.X for scene-level state, self.X stays for
    # controller-owned state)
    # -----------------------------------------------------------------
    def load_map(self, enter_edge=None, target_cell=None):
        if target_cell:
            self.c, self.r = target_cell
        m = WD.gen_map(self.c, self.r)
        self._map_data = m
        self.scene.enemies = []
        # ECS adapter (Task 12): the legacy enemy list is rebuilt on every map
        # enter, so the parallel enemy entities from the previous map must be
        # destroyed + the id()->Entity map cleared. Otherwise the entity layer
        # would keep stale entities for WorldEnemy objects that no longer exist
        # (the old Python objects are gone, so id() may even recycle). The hero
        # entities persist across maps (the party is not rebuilt by _load_map).
        for ee_id in list(self.scene._entity_for_enemy.values()):
            self.scene.world.destroy(ee_id.eid if hasattr(ee_id, "eid") else ee_id)
        self.scene._entity_for_enemy = {}
        self.scene._drops_legacy = []
        # clear summon/trap entities on map enter so a stale summon from the last
        # cell doesn't follow the player (Task A3).
        self.scene._summons = []
        self.scene._traps = []
        # clear hold-to-aim state on map enter (Task B2) so a stale aim from the
        # previous cell doesn't carry across the transition (the held key is
        # released by the player, but the state is defensive-cleared anyway).
        self.scene._aim_skill = None
        self.scene._aim_held_key = None
        self.scene._aim_t = 0.0
        # clear AA targets on map enter (Task B3) so a stale AA target from the
        # previous cell's enemies doesn't carry across the transition (the
        # target enemy belongs to the old map — a ref to it would be invalid).
        for p in self.scene.party:
            if p is not None:
                p.aa_target = None
        # dynamic weather: re-evaluate the per-cell weather state from the current
        # day phase on every map enter. Stored on the scene (NOT in gen_map — the
        # MapRenderer cache is keyed on (c,r) only, and weather is a live overlay
        # + combat modifier, not a baked map property). Reset the storm strike
        # timer so a fresh map's storm cadence is independent of the last.
        self.scene._weather = WD.weather_for(self.c, self.r, self.scene._world_time)
        self.scene._storm_strike_t = 6.0   # first storm strike ~6s after entering a storm map
        # reset any stale boss intro/defeat banner timers on a non-boss map so a
        # cinematic from a previous boss arena doesn't bleed onto the wrong map
        if not m["is_boss"]:
            self.scene._boss_intro_t = 0.0
            self.scene._boss_intro_name = ""
            self.scene._boss_defeat_t = 0.0
            self.scene._boss_defeat_name = ""
        # treasure chests on this map (open on walk-over): a reward pickup that
        # gives exploration a point beyond killing enemies. Chests the player
        # already opened on a prior visit are restored as opened (persisted in
        # ow_chests_opened) so they can't be re-looted on revisit.
        cid = WD.cell_id(self.c, self.r)
        opened_idx = set(self.scene.game.player.ow_chests_opened.get(cid, []))
        self.scene.chests = [dict(x=x, y=y, kind=kind, opened=(i in opened_idx))
                       for i, (x, y, kind) in enumerate(m.get("chests", []))]
        # breakable props on this map (shatter on attack/dash, drop loot). They
        # are not persisted — a fresh map regenerates them, so a player can
        # re-break them on revisit (the loot is small, so this is fine).
        self.scene.breakables = [dict(x=x, y=y, kind=kind, loot=loot, broken=False)
                           for (x, y, kind, loot) in m.get("breakables", [])]
        # water/bridges/landmark/village (Task C3) — read the STATIC gen_map
        # features. Water rects are appended to the obstacles list so the existing
        # collision check (self._map_data["obstacles"]) treats them as walls
        # (impassable, like obstacles); bridges are passable (NOT appended). The
        # water/bridge rects are also kept on the scene for the draw loop. A copy
        # of the obstacles list is NOT needed — gen_map returns a fresh list per
        # cell, so appending water to it doesn't mutate a cached map (the
        # MapRenderer cache stores a rendered Surface, not the dict).
        self.scene._water = list(m.get("water", []))
        self.scene._bridges = list(m.get("bridges", []))
        self._landmark = m.get("landmark")
        self._village = m.get("village")
        # NPC (Task E1) — spawn the village NPC at the village's npc_spawn (from
        # C3's gen_map). The NPC is a simple entity: a name + quest_id + dialogue
        # (from NPCS[biome]) + the x/y pos. Drawn in the drawables (a small sprite
        # + a name tag); interact on walk-up + F (see the event loop in update).
        # The dialogue is a UI overlay (NOT a pause — the world keeps updating
        # behind it; the dialogue box just draws on top in draw).
        self.scene._npc = None
        self.scene._dialogue = None
        if self._village is not None:
            biome = self._village.get("biome", WD.cell_biome(self.c, self.r))
            npc_data = NPCS.get(biome)
            if npc_data is not None:
                nx, ny = self._village["npc_spawn"]
                self.scene._npc = {"x": float(nx), "y": float(ny),
                             "biome": biome,
                             "name": npc_data["name"],
                             "quest_id": npc_data["quest_id"],
                             "dialogue": list(npc_data["dialogue"])}
        # append the water rects to the obstacles list so the existing collision
        # check treats them as walls (impassable). The bridges are passable, so
        # they are NOT appended (the hero walks through them).
        if self.scene._water:
            m["obstacles"].extend(self.scene._water)
        # lore float on the first visit to this cell's landmark — fired in
        # _load_map (not in _draw_landmark) so the player sees it on cell entry
        # even if the landmark is off-screen on the first draw frame (the float
        # is at the landmark's world pos; if fired in draw, an off-screen
        # landmark would spawn an off-screen float that fades unseen + the
        # ow_landmarks_seen gate would prevent a re-fire). Tracked per cell id
        # in ow_landmarks_seen so revisiting a cell doesn't re-show the lore.
        if self._landmark is not None:
            cid = WD.cell_id(self.c, self.r)
            if cid not in self.scene.game.player.ow_landmarks_seen:
                self.scene.game.player.ow_landmarks_seen.append(cid)
                biome = self._landmark.get("biome", WD.cell_biome(self.c, self.r))
                lore = LANDMARK_LORE.get(biome, "")
                if lore:
                    pal = WD.BIOMES.get(biome, {})
                    col = pal.get("accent", (230, 220, 180))
                    self.scene.floats.append(FloatText(self._landmark["x"],
                                                self._landmark["y"] - 50,
                                                lore, col, size=18, life=2.5))
        # hidden rift mini-dungeon: read the per-cell secret from gen_map. A
        # cleared rift stays cleared (persisted in ow_secrets_done) so the
        # player can't re-trigger the wave for infinite SR/SSR chests. Reset
        # the active seal + wave state on every map enter so a stale seal from
        # a previous map doesn't bleed onto the new one (the wipe-respawn
        # teleport_to(0,0) hits this path too, so the seal breaks on a wipe).
        self._rift_secret = m.get("secret")
        cid = WD.cell_id(self.c, self.r)
        if self._rift_secret is not None and cid in self.scene.game.player.ow_secrets_done:
            self._rift_done = True     # already cleared this visit
        else:
            self._rift_done = False
        self._rift_active = False
        self._rift_enemies = []
        level = WD.cell_level(self.c, self.r, ng_cycle=self.scene.game.player.ng_cycle)
        # the active hero entry point (offset slightly inward from the edge so
        # the hero slides into the new map instead of snapping)
        ep = WD.entry_point(enter_edge) if enter_edge else (WD.MAP_W // 2, WD.MAP_H // 2)
        # place the active hero
        if self.scene.party[self.scene.active]:
            self.scene.party[self.scene.active].x = ep[0]
            self.scene.party[self.scene.active].y = ep[1]
            self.scene.party[self.scene.active].vx = 0
            self.scene.party[self.scene.active].vy = 0
            # snap the camera onto the hero immediately so the transition is a
            # clean slide rather than a flying pan from the previous map
            self.scene.camera.x = max(0, min(WD.MAP_W - self.scene.camera.vw, ep[0] - self.scene.camera.vw / 2))
            self.scene.camera.y = max(0, min(WD.MAP_H - self.scene.camera.vh, ep[1] - self.scene.camera.vh / 2))
            self.scene.map_enter_t = 0.45
            # ensure the active hero starts a map with usable energy (the
            # "skills don't recover" fix: a hero loaded from save with stale low
            # energy should top up to ENERGY_START on map enter)
            a = self.scene.party[self.scene.active]
            if a and a.hero.energy < ENERGY_START:
                a.hero.energy = min(ENERGY_START, a.hero.max_energy)
        # pre-render the new map's surface on a background thread so the first
        # visit doesn't stall the frame (the render is ~10ms but a fresh map's
        # ground-base build can spike). We render synchronously here but the
        # MapRenderer caches the result, so revisits are instant.
        self.scene._map_surf = self.map_renderer.get_locked(self.c, self.r,
                                                      getattr(self.scene, "_warm_lock", None))
        self.scene._map_cell = (self.c, self.r)
        # spawn enemies
        if not m["is_boss"]:
            pool, _ = WD.ROW_ENEMIES[self.r]
            # at night (day phase 0.4..0.95) enemies are tougher: +1 level so
            # the world feels more dangerous after dark (better drops follow from
            # the higher-level enemy gold/xp scaling). The window matches the
            # _night_overlay visual-darkening window so the danger cue and the
            # visual cue agree (was 0.5, leaving a 0.4-0.5 slice where the world
            # looked dark but enemies weren't tougher).
            night_bonus = 1 if 0.4 <= self.scene._world_time <= 0.95 else 0
            # Champion-as-enemy: ~16% of minions spawn as a random LoL champion
            # (with its real kit + sprite) instead of a jungle mob. A rare,
            # memorable encounter — the player meets the roster in the wild.
            champ_pool, _ = _get_champion_enemy_pool()
            for (sx, sy) in m["spawns"]:
                if champ_pool and random.random() < 0.16:
                    eid = random.choice(champ_pool)
                else:
                    eid = random.choice(pool)
                en = WorldEnemy(eid, sx, sy, level + night_bonus, is_boss=False)
                self.scene.enemies.append(en)
                # ECS adapter (Task 12): spawn a parallel enemy entity that
                # tracks this WorldEnemy. Match the level/is_boss args used in
                # the WorldEnemy(...) call above.
                ee = spawn_enemy(self.scene.world, en.id,
                                 level=level + night_bonus, is_boss=False,
                                 x=en.x, y=en.y)
                self.scene._entity_for_enemy[id(en)] = ee
        else:
            # Task E2: gate the boss on its story quest. A biome-boss quest is
            # "active" when the player has accepted it from the NPC (the dialogue
            # acceptance in _advance_dialogue sets story_progress[quest_id] to
            # "active"). The final-boss quest (demon_king) is active only when
            # all 5 biome-boss quests are complete (the chain - see
            # _is_quest_active). Until the quest is active, the boss arena is
            # SEALED: no boss spawns (the arena is empty - the player can still
            # walk in + explore, just no boss to fight) + a "sealed" float at the
            # arena center tells the player to seek the biome's NPC. The gate is
            # on quest acceptance, NOT completion, so the boss spawns the moment
            # the NPC gives the quest. The gate does NOT block exploration: the
            # cell loads, the map renders, the player walks in - just no boss.
            # This keeps the 20/20 suite green (it teleports into the boss cell
            # without the quest; the gate seals the boss but doesn't crash).
            biome = WD.cell_biome(self.c, self.r)
            # Each row's boss cell (column 9) is gated by the row's biome-boss
            # quest (STORY_BIOME_QUEST[biome]). The void row's boss (9,4) is the
            # Demon King - the void_boss quest (the 5th biome-boss) gates it.
            # The void_boss quest is available when castle_boss is complete (the
            # chain), so the Demon King unseals only after the 4 biome bosses
            # before it are cleared + the void NPC gives the void_boss quest.
            # The demon_king quest (the 6th/final) is the chain's end marker -
            # it completes when the Demon King dies (the same kill as the
            # void_boss quest); see the boss-defeat handler. It is NOT a separate
            # gate (the Demon King is the void row's boss, gated by void_boss).
            quest_id = STORY_BIOME_QUEST.get(biome)
            if quest_id is not None and not self.scene._is_quest_active(quest_id):
                # sealed - skip the boss spawn + show a "seek the NPC" float at
                # the arena center (the boss spawn pos from gen_map). The float
                # is short-lived (2.5s) so it doesn't linger on a long stay; the
                # cell still loads (no return) so the player can explore the
                # arena + read the seal message.
                bx, by = m["boss"]
                npc_name = NPCS.get(biome, {}).get("name", "the NPC")
                self.scene.floats.append(FloatText(
                    bx, by - 40,
                    f"SEALED - seek {npc_name} for the quest",
                    (220, 180, 120), size=20, life=2.5))
                self.scene.set_message(
                    f"The arena is sealed. Seek {npc_name} in the {biome} village.",
                    3.0)
            else:
                _, boss_id = WD.ROW_ENEMIES[self.r]
                # Champion-as-enemy: ~35% of bosses spawn as a random SSR/SR
                # champion (boss-tier scaled, real kit + sprite) instead of the
                # row's villain boss. The villain boss still anchors the story
                # quest, so a champion boss only spawns when the quest is active
                # AND the row's villain hasn't been cleared yet — on a rematch
                # (cleared) the champion boss is the encounter. This keeps the
                # story chain intact (the villain boss is the first-clear fight)
                # while making boss arenas occasionally a champion duel.
                _, champ_boss_pool = _get_champion_enemy_pool()
                cid = WD.cell_id(self.c, self.r)
                already_cleared = cid in set(self.scene.game.player.ow_bosses_cleared)
                if (champ_boss_pool and already_cleared
                        and random.random() < 0.35):
                    boss_id = random.choice(champ_boss_pool)
                bx, by = m["boss"]
                en = WorldEnemy(boss_id, bx, by, level + 6, is_boss=True)
                self.scene.enemies.append(en)
                # ECS adapter (Task 12): spawn a parallel enemy entity that
                # tracks this boss WorldEnemy. Match the level/is_boss args.
                ee = spawn_enemy(self.scene.world, en.id,
                                 level=level + 6, is_boss=True,
                                 x=en.x, y=en.y)
                self.scene._entity_for_enemy[id(en)] = ee
                # boss intro cinematic: a name banner + a brief slow-mo the first time
                # the player enters this boss arena. Skips on a revisit (re-entering a
                # cleared arena shouldn't replay the intro).
                boss_name = ENEMIES_DB.get(boss_id, {}).get("name", "Boss")
                self.scene._boss_intro_t = 1.6
                self.scene._boss_intro_name = boss_name
                audio.play("boss_intro", 0.7)
        # reset camera to the active hero (clamped; the edge-entry case already
        # snapped it above, this covers teleport-to and initial load)
        a = self.scene.party[self.scene.active]
        if a:
            self.scene.camera.x = max(0, min(WD.MAP_W - self.scene.camera.vw, a.x - self.scene.camera.vw / 2))
            self.scene.camera.y = max(0, min(WD.MAP_H - self.scene.camera.vh, a.y - self.scene.camera.vh / 2))
        # (map surface already rendered + cached above; keep the cell ref current)
        self.scene._map_surf = self.map_renderer.get_locked(self.c, self.r,
                                                      getattr(self.scene, "_warm_lock", None))
        self.scene._map_cell = (self.c, self.r)
        # discover: a NEW cell advances the 'explore' quest; any map enter
        # (walk or teleport) reveals the neighbors so the frontier grows and
        # the teleport overlay shows reachable cells (was only run once in
        # __init__, capping the discoverable world at ~3 cells).
        cid = WD.cell_id(self.c, self.r)
        if cid not in self.scene.game.player.ow_discovered:
            self.scene.game.player.ow_discovered.append(cid)
            self.scene.game.player.quest_progress("explore", 1)
        # 'explore' also counts revisits so the daily quest stays completable for
        # a mid/late-game player who has already discovered all 50 maps
        self.scene.game.player.quest_progress("explore", 1)
        # reveal the neighbors of the new cell so the minimap shows the
        # reachable frontier (not just cells the player has physically stood in)
        self.discover_neighbors()
        self.scene._persist_party()
        self.scene.game.player.ow_current = [self.c, self.r]
        if self.scene.game.player.settings.get("auto_save", True):
            self.scene.game.player.save()
        # start the looping biome ambience on map enter (a quiet bed so the
        # world isn't silent between hits). Respects the master sound toggle.
        # When the weather is rain/storm, switch the ambience bed to the rain
        # loop so the world sounds wet; thunder one-shots fire from the per-frame
        # storm-strike path (see update).
        if self.scene.game.player.settings.get("sound", True):
            biome = WD.cell_biome(self.c, self.r)
            if self.scene._weather == "rain" or self.scene._weather == "storm":
                audio.set_ambience(True, volume=0.30, biome=biome, weather="rain")
            else:
                audio.set_ambience(True, volume=0.22, biome=biome)

    def discover_neighbors(self):
        for (nc, nr) in WD.neighbors(self.c, self.r):
            cid = WD.cell_id(nc, nr)
            if cid not in self.scene.game.player.ow_discovered:
                self.scene.game.player.ow_discovered.append(cid)

    def transition(self, edge):
        # find the neighbor in that direction
        c, r = self.c, self.r
        if edge == "right" and c < WD.GRID_W - 1:   nc, nr = c + 1, r
        elif edge == "left" and c > 0:              nc, nr = c - 1, r
        elif edge == "bottom" and r < WD.GRID_H - 1: nc, nr = c, r + 1
        elif edge == "top" and r > 0:               nc, nr = c, r - 1
        else:
            return  # walled edge
        # opposite entry edge
        opp = {"left": "right", "right": "left", "top": "bottom", "bottom": "top"}[edge]
        # direction of travel — used to slide the fade in the same direction
        self.scene._enter_dir = edge
        self.scene._persist_party()
        # pre-warm the destination map's surface so the transition frame doesn't
        # stall on the first visit. Use the lock-aware get so we never block on
        # the background pre-warm worker (worst case: a throwaway render this
        # frame, cached one next frame).
        self.map_renderer.get_locked(nc, nr, getattr(self.scene, "_warm_lock", None))
        self.load_map(enter_edge=opp, target_cell=(nc, nr))
        # a soft whoosh on edge transitions so a map change has an audible cue
        audio.play("skill", 0.25)
        self.scene.set_message(f"Entering {WD.cell_name(nc, nr)}")

    def teleport_to(self, c, r):
        self.scene._persist_party()
        self.scene.teleport = None
        self.scene._enter_dir = None
        self.load_map(enter_edge=None, target_cell=(c, r))
        # center the hero
        if self.scene.party[self.scene.active]:
            self.scene.party[self.scene.active].x = WD.MAP_W // 2
            self.scene.party[self.scene.active].y = WD.MAP_H // 2
        # a UI warp-confirm cue so the teleport isn't silent
        audio.play("menu_click", 0.4)
        self.scene.set_message(f"Teleported to {WD.cell_name(c, r)}")
