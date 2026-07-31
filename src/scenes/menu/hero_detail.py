"""Hero detail scene."""
import pygame

from src.core.scene import Scene
from src.ui import (WIDTH, WHITE, DIM, GOLD, HP_RED, MP_BLUE, XP_PURPLE, Button,
                    draw_panel, draw_bar, draw_stars, rarity_color, text, f)
from src.entities import load_portrait, load_item_icon
from src.data.constellation import hero_constellation_perks
from src.data.equipment import EQUIPMENT_DB, EQUIPMENT_SETS
from src.data.heroes import HERO_ASSETS, HERO_BY_ID, HERO_LORE, ULTIMATE_VARIANTS, hero_abilities
from src.data.skills import SKILLS_DB
from src.data.tuning import ASSET_DIR, MAX_ASCENSION, xp_to_next
import src.build.champions as _CH
import src.audio as audio
class HeroDetailScene(Scene):
    """View a hero, add/remove from team, ascend, equip items, swap skins."""
    def __init__(self, game, hero_id):
        super().__init__(game)
        self.hero_id = hero_id
        self.back_btn = Button((40, 40, 140, 48), "Back", (60, 60, 90), (90, 90, 130), size=20)
        self.team_btn = Button((WIDTH - 260, 600, 220, 56), "Add to Team", (60, 120, 80), (90, 180, 110), size=20)
        self.ascend_btn = Button((WIDTH - 260, 520, 220, 56), "Ascend", (150, 60, 130), (200, 90, 170), size=20)
        self.evolve_btn = Button((WIDTH - 260, 460, 220, 50), "Evolution Tree",
                                 (110, 70, 150), (170, 110, 210), size=16)
        self.tab = "equip"   # equip | stats
        self.t = 0
        self.equip_slots = ["weapon", "armor", "accessory"]
        # cached draw-state; initialized here so update()/draw() are safe even
        # if called before the first full draw() (goto swaps mid-frame).
        self._item_rects = []
        # "Team Full!" flash timer: the Add-to-Team button briefly shows this
        # when the team is full instead of silently overwriting a slot.
        self._team_full_t = 0.0
        # skin selector state. Skins come from the baked champion metadata
        # (champions.CHAMPION_BY_KEY); the equipped skin index lives on the
        # hero record (rec["skin"], default 0 = Original). Left/right arrows
        # under the portrait cycle the skin + re-render the portrait.
        _c = _CH.CHAMPION_BY_KEY.get(hero_id)
        self._skins = _c["skins"] if _c else [{"name": "Original", "id": 0, "index": 0}]
        self._skin_rects = []  # [(rect, idx), ...] for click hit-testing

    def update(self, dt, events):
        self.t += dt
        # the "Team Full!" flash reverts to the normal label after it expires
        if self._team_full_t > 0:
            self._team_full_t = max(0, self._team_full_t - dt)
            if self._team_full_t <= 0:
                in_team_now = self.hero_id in self.game.player.team
                self.team_btn.label = "Remove from Team" if in_team_now else "Add to Team"
        mp = pygame.mouse.get_pos()
        mdown = pygame.mouse.get_pressed()[0]
        self.back_btn.update(mp, mdown)
        self.team_btn.update(mp, mdown)
        self.ascend_btn.update(mp, mdown)
        self.evolve_btn.update(mp, mdown)
        hid = self.hero_id
        in_team = hid in self.game.player.team
        # Adventure mode (Task D2): the party is locked for the run — the team
        # was set via the roster BEFORE entering adventure, and mid-run roster
        # changes are refused. Grey the Add/Remove button + show "Locked for
        # Run" so the player sees the lock instead of a silent no-op. The 1-4
        # in-world swap (WorldScene._switch) is NOT affected (it changes only
        # the active index, not the roster).
        adv_locked = self.game.player.mode == "adventure"
        if adv_locked:
            self.team_btn.label = "Locked for Run"
            self.team_btn.text_color = (120, 120, 140)
        elif self._team_full_t <= 0:
            self.team_btn.label = "Remove from Team" if in_team else "Add to Team"
            self.team_btn.text_color = WHITE
        rec = self.game.player.owned[hid]
        asc = rec.get("ascension", 0)
        can_ascend = rec["dupes"] > 0 and asc < MAX_ASCENSION
        self.ascend_btn.text_color = WHITE if can_ascend else (150, 150, 150)
        # invalidate the cached stat instance when equipment/level changes
        self._stat_hid = None
        for e in events:
            if self.back_btn.clicked(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                self.game.back("roster")
            if self.team_btn.clicked(e):
                # Adventure mode: refuse the team edit (the party is locked for
                # the run). Play a soft "hit" so the player hears the refusal
                # instead of a silent no-op.
                if adv_locked:
                    audio.play("hit", 0.2)
                    continue
                if in_team:
                    self.game.player.team = [t for t in self.game.player.team if t != hid]
                    if len(self.game.player.team) < 3:
                        self.game.player.team.append(None)
                else:
                    # add to the first empty slot; if the team is full (no None),
                    # refuse instead of silently overwriting a slot — that would
                    # evict the hero in that slot without telling the player.
                    if None in self.game.player.team:
                        idx = self.game.player.team.index(None)
                        self.game.player.team[idx] = hid
                    else:
                        # team full: flash the button label briefly so the player
                        # sees the team is full rather than losing a hero silently
                        self.team_btn.label = "Team Full!"
                        self._team_full_t = 1.2
                        audio.play("hit", 0.3)
                        return
                self.game.player.save()
                audio.play("menu_click")
            if self.ascend_btn.clicked(e) and can_ascend:
                rec["dupes"] -= 1
                rec["ascension"] = asc + 1
                self.game.player.save()
                audio.play("ultimate", 0.5)
            # skin selector arrows (left/right under the portrait)
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for rect, idx in self._skin_rects:
                    if rect.collidepoint(e.pos):
                        rec["skin"] = idx
                        self.game.player.save()
                        audio.play("menu_click")
                        break
            if self.evolve_btn.clicked(e):
                # jump to the world's evolve overlay for this hero
                self.game.goto("world")
                from src.scenes.world import EvolveOverlay
                self.game.scene.evolve = EvolveOverlay(self.game)
                # select this hero in the overlay
                try:
                    self.game.scene.evolve.sel = self.game.scene.evolve.order.index(hid)
                except Exception:
                    pass
                audio.play("menu_click", 0.3)
            # equip item click: click a slot then an item
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # clicking an equipment slot
                for si, slot in enumerate(self.equip_slots):
                    sr = pygame.Rect(680 + si * 180, 200, 160, 160)
                    if sr.collidepoint(e.pos):
                        # unequip
                        if rec["equipment"].get(slot):
                            self.game.player.unequip(hid, slot)
                            self.game.player.save()
                            audio.play("menu_click")
                        return
                # clicking an inventory item to equip
                for it_rect, item_id in self._item_rects:
                    if it_rect.collidepoint(e.pos):
                        if item_id in self.game.player.equipment_inv:
                            self.game.player.equip(hid, item_id)
                            self.game.player.save()
                            audio.play("menu_click")
                        return

    def draw(self, surf):
        surf.fill(BG_DARK)
        hid = self.hero_id
        hd = HERO_BY_ID[hid]
        rec = self.game.player.owned[hid]
        # portrait big — the equipped skin's splash (rec["skin"], default 0)
        skin_idx = rec.get("skin", 0)
        p = load_portrait(hid, skin_idx, 360)
        draw_panel(surf, (40, 110, 400, 480))
        surf.blit(p, (60, 130))
        text(surf, hd["name"], 36, WHITE, (240, 510), center=True)
        text(surf, hd["title"], 20, DIM, (240, 548), center=True)
        nstars = 3 if hd['rarity'] == "SSR" else (2 if hd['rarity'] == "SR" else 1)
        draw_stars(surf, 240 - 30, 576, nstars, size=12)
        # skin selector: left/right arrows + the equipped skin's name. Cycles
        # the champ's skins (from the baked metadata) + saves the choice on the
        # hero record (rec["skin"]). The portrait above re-renders per skin.
        self._skin_rects = []
        if len(self._skins) > 1:
            skin_idx = rec.get("skin", 0)
            cur = next((s for s in self._skins if s["index"] == skin_idx), self._skins[0])
            # only show skins whose splash art exists on disk
            import os
            avail = [s for s in self._skins
                     if os.path.exists(os.path.join(ASSET_DIR, "characters", hid,
                                                    "skins", f"{s['index']}.jpg"))
                     or s["index"] == 0]
            if avail:
                cur = next((s for s in avail if s["index"] == skin_idx), avail[0])
                ci = avail.index(cur)
                prev_s = avail[(ci - 1) % len(avail)]
                next_s = avail[(ci + 1) % len(avail)]
                # arrow buttons + name, centered under the stars
                ay = 596
                pygame.draw.polygon(surf, (180, 200, 240),
                                    [(150, ay), (150, ay + 16), (138, ay + 8)])
                pygame.draw.polygon(surf, (180, 200, 240),
                                    [(330, ay), (330, ay + 16), (342, ay + 8)])
                self._skin_rects = [
                    (pygame.Rect(132, ay - 4, 24, 24), prev_s["index"]),
                    (pygame.Rect(324, ay - 4, 24, 24), next_s["index"]),
                ]
                text(surf, cur["name"], 13, (200, 220, 255), (240, ay + 22), center=True)
        # ascension pips
        asc = rec.get("ascension", 0)
        text(surf, f"Ascension {asc}/{MAX_ASCENSION}  (dupes: {rec['dupes']})", 16, (255, 180, 220), (240, 600), center=True)
        # constellation nodes (C1-C6) — 6 pips in a row, lit for each unlocked
        # star, with the NEXT perk's description under the Ascend button so the
        # player sees what the next star will do before spending a dupe.
        # (Task A2) constellation perks come from HERO_ASSETS (same data, one bundle).
        hero_assets = HERO_ASSETS.get(hid)
        perks = hero_assets["constellation"] if hero_assets else hero_constellation_perks(hd)
        cx0 = 240 - 90   # center 6 pips of width ~30 each
        for i in range(6):
            cx = cx0 + i * 30
            unlocked = i < asc
            col = (255, 120, 200) if unlocked else (70, 60, 80)
            pygame.draw.circle(surf, col, (cx, 622), 7)
            if unlocked:
                pygame.draw.circle(surf, (255, 220, 240), (cx, 622), 7, 2)
        # next perk description (the one the next Ascend click will unlock)
        if asc < 6:
            np = perks[asc]
            text(surf, f"Next (C{asc+1}): {np['name']} - {np['desc']}", 12,
                 (200, 180, 220), (240, 640), center=True)
        else:
            text(surf, "Constellation MAX", 12, (255, 220, 240), (240, 640), center=True)
        # lore panel: bio + centered italic quote, below the portrait (space at y~620+)
        # (Task A2) lore comes from HERO_ASSETS (same data, one bundle).
        lore = hero_assets["lore"] if hero_assets else HERO_LORE.get(hid)
        if lore:
            # "italic" via a SysFont with italic=True, cached so we don't rebuild it each frame.
            if not hasattr(self, "_lore_font"):
                self._lore_font = pygame.font.SysFont("dejavusans,arial", 16, italic=True)
            # bio, word-wrapped to the left panel width (x 40..440, ~400 px)
            bio = lore["bio"]
            words = bio.split(" ")
            lines = []
            cur = ""
            for w in words:
                trial = cur + " " + w if cur else w
                if self._lore_font.size(trial)[0] <= 380:
                    cur = trial
                else:
                    if cur:
                        lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
            by = 624
            for ln in lines[:3]:
                text(surf, ln, 14, DIM, (60, by))
                by += 18
            # centered italic quote (word-wrapped so long quotes don't overflow the panel)
            qt = lore["quote"]
            qwords = qt.split(" ")
            qlines = []
            qcur = ""
            for w in qwords:
                trial = qcur + " " + w if qcur else w
                if self._lore_font.size(trial)[0] <= 380:
                    qcur = trial
                else:
                    if qcur:
                        qlines.append(qcur)
                    qcur = w
            if qcur:
                qlines.append(qcur)
            qy = by + 8
            for ln in qlines:
                t = self._lore_font.render(ln, True, (220, 200, 160))
                r = t.get_rect(midtop=(240, qy))
                sh = self._lore_font.render(ln, True, (0, 0, 0))
                surf.blit(sh, (r.x + 2, r.y + 2))
                surf.blit(t, r)
                qy += 20
        # stats panel
        draw_panel(surf, (460, 110, 780, 360))
        # cache the hero instance per hero id so we don't rebuild it every frame
        if getattr(self, "_stat_hid", None) != hid:
            self._stat_hid = hid
            self._stat_inst = self.game.player.get_hero_instance(hid)
        h_inst = self._stat_inst
        text(surf, "Stats", 24, GOLD, (480, 124))
        stats = [("HP", h_inst.max_hp, HP_RED), ("ATK", h_inst.atk, (255, 120, 80)),
                 ("DEF", h_inst.defn, (140, 180, 255)), ("SPD", h_inst.spd, (180, 240, 220)),
                 ("MP", h_inst.max_mp, MP_BLUE), ("Crit", f"{int(h_inst.crit_chance*100)}%", (255, 220, 120))]
        # stat rows are kept in the LEFT of the panel (x 460..680) so the bars
        # and values are not obscured by the equipment slots on the right.
        for i, (lbl, val, col) in enumerate(stats):
            y = 160 + i * 36
            text(surf, lbl, 20, WHITE, (470, y))
            if isinstance(val, int):
                # stat bar (relative) — narrow so it stays clear of the slots
                frac = min(1, val / 400)
                draw_bar(surf, (540, y + 4, 110, 20), frac, col)
            text(surf, str(val), 20, col, (660, y))
        # level + xp (left zone, below the stat rows)
        text(surf, f"Level {rec['level']}", 22, WHITE, (470, 384))
        xp_need = xp_to_next(rec["level"])
        draw_bar(surf, (540, 390, 110, 18), rec["xp"] / max(1, xp_need), XP_PURPLE)
        text(surf, f"XP {rec['xp']}/{xp_need}", 13, DIM, (660, 386))
        # ultimate / passive / skills / evo — moved up inside the panel (which
        # ends at y=470) so they are no longer overlapped by the inventory list.
        # (Task A2) read the per-hero ultimate + skills from HERO_ASSETS — the
        # single source of truth — falling back to the combat dicts only if the
        # manifest is somehow missing this hero.
        if hero_assets:
            ult_entry = next((s for s in hero_assets["skills"]
                              if s["id"] == hd.get("ultimate")), None)
        else:
            ult_entry = None
        ult_var = hero_assets["ultimate"] if hero_assets else (
            ULTIMATE_VARIANTS.get(hd["id"]) if hd.get("ultimate") else None)
        if ult_entry:
            ult_name = ult_entry["name"]
        elif ult_var:
            ult_name = ult_var["name"]
        else:
            ult_name = SKILLS_DB[hd["ultimate"]]["name"] if hd.get("ultimate") else "None"
        ult_desc = ult_var.get("desc", "") if ult_var else ""
        text(surf, f"Ultimate: {ult_name}", 18, (255, 180, 120), (470, 412))
        if ult_desc:
            text(surf, ult_desc, 12, (200, 180, 150), (470, 430))
        # signature passive from HERO_ASSETS (falls back to the instance passive)
        sig = hero_assets["signature"] if hero_assets else None
        pv = sig if sig else h_inst.passive
        if pv:
            text(surf, f"Passive: {pv['name']}", 14, (160, 220, 180), (470, 448))
        # active skills: names from HERO_ASSETS, with a compact how_to_use hint
        # line under each so the player sees the key + aim note at a glance.
        if hero_assets:
            actives = [s for s in hero_assets["skills"] if s["id"] != "basic_attack"
                       and s["type"] != "ultimate"]
        else:
            ab = hero_abilities(hd)
            actives = [{"name": SKILLS_DB[s]["name"] if s and s in SKILLS_DB else "-",
                        "how_to_use": ""} for s in ab]
        # pad to 3 so the HUD line is stable
        while len(actives) < 3:
            actives.append({"name": "-", "how_to_use": ""})
        text(surf, f"Q {actives[0]['name']}  W {actives[1]['name']}  E {actives[2]['name']}",
             13, (200, 220, 255), (470, 466))
        # how_to_use hint line — one compact row of the 3 active keys' aim notes,
        # shown just under the Q/W/E line so the player sees the aim note at a glance.
        hints = [s.get("how_to_use", "") for s in actives[:3]]
        if any(hints):
            compact = "  |  ".join(h.split("—")[1].strip() if "—" in h else h
                                  for h in hints if h)
            if compact:
                text(surf, compact[:90], 10, (150, 170, 200), (470, 482))
        # evolution tree progress
        nn = len(rec.get("evo_nodes", []))
        text(surf, f"Evo {nn}/5  Tier {h_inst.evolve_title()}",
             13, (220, 180, 255), (470, 498))
        # equipment slots
        text(surf, "Equipment", 22, GOLD, (680, 168))
        self._item_rects = []
        for si, slot in enumerate(self.equip_slots):
            sr = pygame.Rect(680 + si * 180, 200, 160, 160)
            # slot frame tinted by whether an item is equipped
            eq = rec["equipment"].get(slot)
            slot_col = (70, 60, 90) if eq else (50, 50, 70)
            pygame.draw.rect(surf, slot_col, sr, border_radius=12)
            pygame.draw.rect(surf, (180, 180, 220), sr, 2, border_radius=12)
            text(surf, slot.upper(), 14, DIM, (sr.centerx, sr.bottom + 6), center=True)
            if eq:
                ic = load_item_icon(eq, 120)
                surf.blit(ic, (sr.centerx - 60, sr.y + 20))
                text(surf, EQUIPMENT_DB[eq]["name"], 13, WHITE, (sr.centerx, sr.bottom + 24), center=True)
        # active set bonus indicator (below the equipment slots)
        set_name = h_inst.set_name()
        if set_name:
            set_def = next((v for v in EQUIPMENT_SETS.values() if v["name"] == set_name), None)
            if set_def:
                text(surf, f"Set: {set_name} ({set_def['desc']})", 13, (255, 220, 120), (680, 372))
        # equipment inventory list — moved below the stats panel (y=490+) so it
        # no longer overlaps the skills/evo text that sat at y=484/504.
        text(surf, "Inventory (click to equip)", 20, GOLD, (460, 484))
        ex, ey = 460, 504
        for i, item_id in enumerate(self.game.player.equipment_inv[:8]):
            col = i % 4
            row = i // 4
            r = pygame.Rect(ex + col * 100, ey + row * 100, 88, 88)
            item = EQUIPMENT_DB[item_id]
            pygame.draw.rect(surf, (40, 40, 60), r, border_radius=10)
            pygame.draw.rect(surf, rarity_color(item["rarity"]), r, 2, border_radius=10)
            ic = load_item_icon(item_id, 64)
            surf.blit(ic, (r.x + 12, r.y + 12))
            # stat string under the icon
            stat_str = " ".join(f"+{v}{k[0].upper()}" for k, v in item["stats"].items())
            text(surf, stat_str, 10, (200, 220, 255), (r.centerx, r.bottom - 12), center=True)
            self._item_rects.append((r, item_id))
        # buttons
        self.back_btn.draw(surf)
        self.team_btn.draw(surf)
        self.ascend_btn.draw(surf)
        self.evolve_btn.draw(surf)


