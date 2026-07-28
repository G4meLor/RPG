"""
Aetheria Gacha - Player state & save/load
Inventory, equipment, ascension, shop, achievements and statistics.
"""
import os
import json
import random
import time

import data as D
from entities import Hero

SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves")
SAVE_FILE = os.path.join(SAVE_DIR, "save.json")


class Player:
    def __init__(self):
        self.gems = D.STARTING_GEMS
        self.gold = D.STARTING_GOLD
        self.owned = {}          # hero_id -> {level, xp, dupes, ascension, equipment, evolve}
        self.team = list(D.STARTING_TEAM)
        self.gacha_pity = {}     # banner_id -> pulls since last SSR (per-banner pity)
        self.total_pulls = 0
        # inventory
        self.inventory = dict(D.STARTING_INVENTORY)      # item_id -> count
        self.equipment_inv = []                          # list of equipment ids owned
        # stats / achievements
        self.stats = dict(battles_won=0, battles_lost=0, total_pulls=0,
                          enemies_defeated=0, gold_earned=0, gems_earned=0,
                          bosses_defeated=0, daily_clears=0)
        self.last_login_day = None
        self.login_streak = 0
        # daily quests
        self.quests = {}                 # quest_id -> {progress, claimed}
        self.quests_last_reset = None    # date string
        # achievements unlocked
        self.achievements = []           # list of achievement ids unlocked
        # settings — a rich, persisted config. Keys with defaults are merged on
        # load so older saves pick up new options without losing old ones.
        self.settings = dict(
            sound=True,            # master sound on/off
            sfx_volume=0.7,        # 0..1 master SFX volume
            music_volume=0.5,      # 0..1 (reserved for future music)
            text_speed=1.0,        # 0.5..2.0
            fullscreen=True,       # borderless fullscreen (default on)
            show_fps=False,        # debug FPS overlay
            fps_cap=60,            # target frame rate
            screen_shake=1.0,      # 0..1 shake intensity multiplier
            damage_numbers=True,   # show floating damage text
            reduce_motion=False,   # dampen shake/flashes for accessibility
            show_hints=True,       # controls hint bar
            particle_quality=1.0,  # 0.4..1.0 particle density multiplier
            auto_save=True,        # auto-save on map changes
            colorblind_mode=False, # deuteranopia-safe element palette swap
        )
        # --- open-world state ---
        self.shards = 0                  # soul shards for evolve/ascend
        self.ow_current = [0, 0]         # current grid cell (col, row)
        self.ow_pos = [0, 0]            # active hero pixel pos in current map
        self.ow_discovered = ["0,0"]     # discovered cell ids
        self.ow_party_state = {}         # hero_id -> {hp, energy} persisted across swaps/maps
        self.ow_time = 0.0              # world day/night phase (0..1, 4-min cycle)
        # opened treasure chests per cell, so a chest stays opened after the
        # player leaves and returns (otherwise it's an infinite-loot exploit).
        # Maps "cell_id" -> list of opened chest indices in gen_map order.
        self.ow_chests_opened = {}
        # boss cells the player has already cleared — bosses in these cells pay
        # out a reduced "rematch" reward on re-kill (no infinite gem farming).
        self.ow_bosses_cleared = []     # list of "c,r" cell ids
        # init owned heroes
        for hid in D.STARTING_OWNED:
            self.owned[hid] = dict(level=1, xp=0, dupes=0, ascension=0,
                                  equipment={}, evolve=0, evo_nodes=[])

    # --- heroes ---
    def has_hero(self, hid):
        return hid in self.owned

    def add_hero(self, hid):
        if hid in self.owned:
            self.owned[hid]["dupes"] += 1
            # convert dupe to ascension if below cap, else refund some shards
            if self.owned[hid]["ascension"] < D.MAX_ASCENSION:
                self.owned[hid]["ascension"] += 1
            else:
                self.shards += 5
            return "dupe"
        self.owned[hid] = dict(level=1, xp=0, dupes=0, ascension=0, equipment={},
                               evolve=0, evo_nodes=[])
        return "new"

    def get_hero_instance(self, hid):
        if hid not in self.owned: return None
        hd = D.HERO_BY_ID[hid]
        rec = self.owned[hid]
        return Hero(hd, level=rec["level"], ascension=rec.get("ascension", 0),
                    equipment=rec.get("equipment", {}),
                    evolve=rec.get("evolve", 0),
                    evo_nodes=rec.get("evo_nodes", []))

    # --- evolve (soul-shard ascension to higher tiers) ---
    def evolve_cost(self, hid):
        rec = self.owned.get(hid)
        if not rec: return None
        tier = rec.get("evolve", 0)
        if tier >= D.MAX_EVOLVE:
            return None
        return D.EVOLVE_COST.get(tier + 1, 9999)

    def can_evolve(self, hid):
        cost = self.evolve_cost(hid)
        return cost is not None and self.shards >= cost

    def evolve_hero(self, hid):
        if not self.can_evolve(hid):
            return False
        cost = self.evolve_cost(hid)
        self.shards -= cost
        rec = self.owned[hid]
        rec["evolve"] = rec.get("evolve", 0) + 1
        return True

    # --- evolution tree (branching per-hero skill tree) ---
    def evo_node_cost(self, hid, node_id):
        """Shard cost to unlock a tree node for a hero."""
        rec = self.owned.get(hid)
        if not rec: return None
        hd = D.HERO_BY_ID[hid]
        tree = D.hero_evo_tree(hd)
        node = next((n for n in tree if n["id"] == node_id), None)
        if node is None: return None
        return node.get("cost", 20)

    def can_unlock_evo_node(self, hid, node_id):
        rec = self.owned.get(hid)
        if not rec: return False
        unlocked = set(rec.get("evo_nodes", []))
        if node_id in unlocked:
            return False
        hd = D.HERO_BY_ID[hid]
        tree = D.hero_evo_tree(hd)
        node = next((n for n in tree if n["id"] == node_id), None)
        if node is None: return False
        if not D.evo_node_prereq_met(node, unlocked):
            return False
        return self.shards >= node.get("cost", 20)

    def unlock_evo_node(self, hid, node_id):
        """Unlock a tree node; spend shards and record it. Returns True on success."""
        if not self.can_unlock_evo_node(hid, node_id):
            return False
        cost = self.evo_node_cost(hid, node_id)
        self.shards -= cost
        rec = self.owned[hid]
        nodes = rec.setdefault("evo_nodes", [])
        if node_id not in nodes:
            nodes.append(node_id)
        return True

    def team_heroes(self):
        heroes = []
        for hid in self.team:
            if hid in self.owned:
                heroes.append(self.get_hero_instance(hid))
            else:
                heroes.append(None)
        return heroes

    def team_power(self):
        return sum(h.power() for h in self.team_heroes() if h)

    def set_team(self, ids):
        self.team = [i for i in ids if i in self.owned][:4]
        while len(self.team) < 4:
            self.team.append(None)

    # --- equipment ---
    def add_equipment(self, item_id):
        if item_id in D.EQUIPMENT_DB:
            self.equipment_inv.append(item_id)

    def equip(self, hero_id, item_id):
        if hero_id not in self.owned or item_id not in self.equipment_inv:
            return False
        item = D.EQUIPMENT_DB[item_id]
        slot = item["slot"]
        rec = self.owned[hero_id]
        # return currently equipped item in that slot to inventory
        prev = rec["equipment"].get(slot)
        if prev:
            self.equipment_inv.append(prev)
        rec["equipment"][slot] = item_id
        self.equipment_inv.remove(item_id)
        return True

    def unequip(self, hero_id, slot):
        if hero_id not in self.owned: return False
        rec = self.owned[hero_id]
        prev = rec["equipment"].get(slot)
        if prev:
            self.equipment_inv.append(prev)
            del rec["equipment"][slot]
        return True

    def sell_equipment(self, item_id):
        """Sell an equipment item from inventory for gold. Returns True on success."""
        if item_id not in self.equipment_inv:
            return False
        item = D.EQUIPMENT_DB.get(item_id)
        if not item:
            return False
        self.equipment_inv.remove(item_id)
        self.gold += item.get("sell", item.get("price", 0) // 3)
        return True

    # --- inventory / consumables ---
    def has_item(self, item_id, count=1):
        return self.inventory.get(item_id, 0) >= count

    def use_item(self, item_id):
        if not self.has_item(item_id):
            return False
        self.inventory[item_id] -= 1
        if self.inventory[item_id] <= 0:
            del self.inventory[item_id]
        return True

    def add_item(self, item_id, count=1):
        self.inventory[item_id] = self.inventory.get(item_id, 0) + count

    def sell_item(self, item_id):
        """Sell a consumable from inventory for gold. Returns True on success."""
        if not self.has_item(item_id):
            return False
        item = D.CONSUMABLES_DB.get(item_id)
        if not item:
            return False
        self.use_item(item_id)
        self.gold += item.get("sell", item.get("price", 0) // 3)
        return True

    # --- shop ---
    def buy_consumable(self, item_id):
        item = D.CONSUMABLES_DB.get(item_id)
        if not item: return False
        if self.gold < item["price"]: return False
        self.gold -= item["price"]
        self.add_item(item_id, 1)
        return True

    def buy_equipment(self, item_id):
        item = D.EQUIPMENT_DB.get(item_id)
        if not item: return False
        if self.gold < item["price"]: return False
        self.gold -= item["price"]
        self.add_equipment(item_id)
        return True

    def buy_gems(self, offer_id):
        offer = next((o for o in D.SHOP_GEMS if o["id"] == offer_id), None)
        if not offer: return False
        if self.gold < offer["price"]: return False
        self.gold -= offer["price"]
        self.gems += offer["gems"]
        return True

    # --- rewards ---
    def grant_rewards(self, rewards):
        self.gold += rewards.get("gold", 0)
        self.gems += rewards.get("gems", 0)
        self.stats["gold_earned"] += rewards.get("gold", 0)
        self.stats["gems_earned"] += rewards.get("gems", 0)
        xp = rewards.get("xp", 0)
        if xp:
            for hid in self.team:
                if hid and hid in self.owned:
                    h = self.get_hero_instance(hid)
                    leveled = h.gain_xp(xp)
                    self.owned[hid]["level"] = h.level
                    self.owned[hid]["xp"] = h.xp

    # --- achievements / stats ---
    def record_kill(self, n=1):
        """Tally a world kill (kept for any external callers / future use)."""
        self.stats["enemies_defeated"] = self.stats.get("enemies_defeated", 0) + n

    def record_pulls(self, n):
        self.total_pulls += n
        self.stats["total_pulls"] += n

    # --- daily login (7-day streak) ---
    def check_daily(self):
        """Return (granted, amount, streak) for a daily gem login bonus."""
        today = time.strftime("%Y-%m-%d")
        if self.last_login_day == today:
            return False, 0, self.login_streak
        # streak: if yesterday was the last login, continue the streak; else reset to 1
        import datetime as _dt
        try:
            last = _dt.datetime.strptime(self.last_login_day, "%Y-%m-%d").date() if self.last_login_day else None
            today_d = _dt.datetime.strptime(today, "%Y-%m-%d").date()
            if last and (today_d - last).days == 1:
                self.login_streak += 1
            else:
                self.login_streak = 1
        except Exception:
            self.login_streak = 1
        self.login_streak = min(self.login_streak, 12)
        # escalating bonus: 50, 60, 80, 100, 120, 150, 200, 220, 250, 300, 350, 400 (12 days)
        schedule = [50, 60, 80, 100, 120, 150, 200, 220, 250, 300, 350, 400]
        bonus = schedule[min(self.login_streak - 1, len(schedule) - 1)] if self.login_streak >= 1 else 50
        self.last_login_day = today
        self.gems += bonus
        self.stats["gems_earned"] = self.stats.get("gems_earned", 0) + bonus
        return True, bonus, self.login_streak

    # --- achievements ---
    def unlock_achievement(self, aid):
        if aid in self.achievements:
            return False
        self.achievements.append(aid)
        reward = D.ACHIEVEMENTS.get(aid, {}).get("reward_gems", 0)
        if reward:
            self.gems += reward
            self.stats["gems_earned"] = self.stats.get("gems_earned", 0) + reward
        return True

    def _has_ssr(self):
        return any(D.HERO_BY_ID[h].get("rarity") == "SSR" for h in self.owned)

    def check_achievements(self):
        """Evaluate achievement conditions; return list of newly-unlocked ids."""
        newly = []
        for aid, ach in D.ACHIEVEMENTS.items():
            if aid in self.achievements:
                continue
            if ach["check"](self):
                if self.unlock_achievement(aid):
                    newly.append(aid)
        return newly

    # --- daily quests ---
    def reset_quests_if_needed(self):
        today = time.strftime("%Y-%m-%d")
        if self.quests_last_reset != today:
            self.quests = {}
            for qid, q in D.DAILY_QUESTS.items():
                self.quests[qid] = dict(progress=0, claimed=False, goal=q["goal"])
            self.quests_last_reset = today

    def quest_progress(self, qid, amount=1):
        self.reset_quests_if_needed()
        st = self.quests.get(qid)
        if not st or st.get("claimed"):
            return
        st["progress"] = min(st["goal"], st.get("progress", 0) + amount)

    def claim_quest(self, qid):
        self.reset_quests_if_needed()
        st = self.quests.get(qid)
        if not st or st.get("claimed"):
            return False
        if st.get("progress", 0) < st.get("goal", 1):
            return False
        st["claimed"] = True
        q = D.DAILY_QUESTS[qid]
        self.gems += q["reward_gems"]
        self.stats["gems_earned"] = self.stats.get("gems_earned", 0) + q["reward_gems"]
        # board-clear capstone: when every quest is claimed, grant a daily bonus
        if all(qst.get("claimed") for qst in self.quests.values()):
            self.stats["daily_clears"] = self.stats.get("daily_clears", 0) + 1
            self.gems += 50
            self.shards += 5
            self.stats["gems_earned"] = self.stats.get("gems_earned", 0) + 50
        return True

    # --- save / load ---
    def save(self):
        os.makedirs(SAVE_DIR, exist_ok=True)
        data = {
            "gems": self.gems, "gold": self.gold,
            "owned": self.owned, "team": self.team,
            "gacha_pity": self.gacha_pity, "total_pulls": self.total_pulls,
            "inventory": self.inventory,
            "equipment_inv": self.equipment_inv,
            "stats": self.stats,
            "last_login_day": self.last_login_day,
            "login_streak": self.login_streak,
            "quests": self.quests,
            "quests_last_reset": self.quests_last_reset,
            "achievements": self.achievements,
            "settings": self.settings,
            "shards": self.shards,
            "ow_current": self.ow_current,
            "ow_pos": self.ow_pos,
            "ow_discovered": self.ow_discovered,
            "ow_party_state": self.ow_party_state,
            "ow_time": self.ow_time,
            "ow_chests_opened": self.ow_chests_opened,
            "ow_bosses_cleared": self.ow_bosses_cleared,
            "version": 5,
        }
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls):
        if not os.path.exists(SAVE_FILE):
            return cls()
        try:
            with open(SAVE_FILE) as f:
                d = json.load(f)
            p = cls()
            p.gems = d.get("gems", D.STARTING_GEMS)
            p.gold = d.get("gold", D.STARTING_GOLD)
            p.owned = d.get("owned", {})
            # migrate old records to include ascension/equipment/evolve
            for hid, rec in p.owned.items():
                rec.setdefault("ascension", 0)
                rec.setdefault("equipment", {})
                rec.setdefault("dupes", 0)
                rec.setdefault("evolve", 0)
                rec.setdefault("evo_nodes", [])
            p.team = d.get("team", list(D.STARTING_TEAM))
            # validate team ids still owned
            p.team = [t if t in p.owned else None for t in p.team]
            while len(p.team) < 4:
                p.team.append(None)
            p.gacha_pity = d.get("gacha_pity", {})
            # migrate legacy int pity -> dict on the standard banner
            if not isinstance(p.gacha_pity, dict):
                p.gacha_pity = {"standard": int(p.gacha_pity)} if p.gacha_pity else {}
            p.total_pulls = d.get("total_pulls", 0)
            p.inventory = d.get("inventory", dict(D.STARTING_INVENTORY))
            p.equipment_inv = d.get("equipment_inv", [])
            p.stats = d.get("stats", p.stats)
            # ensure every stat key the game reads/writes exists on old saves
            # (older versions only had a subset; missing keys default to 0)
            for _sk in ("battles_won", "battles_lost", "total_pulls",
                        "enemies_defeated", "gold_earned", "gems_earned",
                        "bosses_defeated", "daily_clears", "treasures_opened"):
                p.stats.setdefault(_sk, 0)
            p.last_login_day = d.get("last_login_day", None)
            p.login_streak = d.get("login_streak", 0)
            p.quests = d.get("quests", {})
            p.quests_last_reset = d.get("quests_last_reset", None)
            p.achievements = d.get("achievements", [])
            p.settings = d.get("settings", p.settings)
            # merge any new default settings keys that older saves lack so the
            # settings menu always shows every option with a sane default
            _defaults = dict(
                sound=True, sfx_volume=0.7, music_volume=0.5, text_speed=1.0,
                fullscreen=False, show_fps=False, fps_cap=60, screen_shake=1.0,
                damage_numbers=True, reduce_motion=False, show_hints=True,
                particle_quality=1.0, auto_save=True, colorblind_mode=False,
            )
            for k, v in _defaults.items():
                p.settings.setdefault(k, v)
            # open-world state (v4+; migrate older saves to defaults)
            p.shards = d.get("shards", 0)
            p.ow_current = d.get("ow_current", [0, 0])
            p.ow_pos = d.get("ow_pos", [0, 0])
            p.ow_discovered = d.get("ow_discovered", ["0,0"])
            p.ow_party_state = d.get("ow_party_state", {})
            p.ow_time = d.get("ow_time", 0.0)
            p.ow_chests_opened = d.get("ow_chests_opened", {})
            p.ow_bosses_cleared = d.get("ow_bosses_cleared", [])
            return p
        except Exception:
            return cls()
