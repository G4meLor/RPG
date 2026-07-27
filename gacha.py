"""
Aetheria Gacha - Gacha / Summoning system
Multi-banner pulls with rate-up, soft + hard pity, guaranteed SR+ in 10-pulls,
duplicate coin-back, and per-banner pity persistence.
"""
import random
import data as D


class GachaSystem:
    """Per-banner summoning. Pity is tracked per banner and persisted on the
    player (player.gacha_pity is now a dict: banner_id -> pulls since last SSR)."""

    def __init__(self, player):
        self.player = player
        # player.gacha_pity may be an int (old save) -> migrate to a dict
        if not isinstance(player.gacha_pity, dict):
            player.gacha_pity = {}
        self.PITY_HARD = D.GACHA_PITY_HARD
        self.SOFT_PITY = D.GACHA_PITY_SOFT
        self.SR_GUARANTEE_EVERY = D.GACHA_SR_GUARANTEE_EVERY

    # --- banner selection -------------------------------------------------
    def banners(self):
        return D.GACHA_BANNERS

    def banner(self, banner_id):
        return D.GACHA_BANNER_BY_ID.get(banner_id, D.GACHA_BANNERS[0])

    # --- cost / affordability --------------------------------------------
    def cost(self, count):
        return D.GACHA_COST["single" if count == 1 else "multi"]["gems"]

    def can_pull(self, count):
        return self.player.gems >= self.cost(count)

    # --- pity helpers -----------------------------------------------------
    def pity(self, banner_id):
        return self.player.gacha_pity.get(banner_id, 0)

    def _set_pity(self, banner_id, value):
        self.player.gacha_pity[banner_id] = max(0, int(value))

    # --- rarity roll ------------------------------------------------------
    def _roll_rarity(self, banner, force_sr_floor=False):
        """Roll a rarity for the given banner. force_sr_floor guarantees SR+."""
        if force_sr_floor:
            # 10th-pull guarantee: SR or SSR only
            r = random.random()
            ssr_share = D.GACHA_RATES["SSR"] / (D.GACHA_RATES["SSR"] + D.GACHA_RATES["SR"])
            return "SSR" if r < ssr_share else "SR"
        r = random.random()
        cum = 0.0
        for rar in ("SSR", "SR", "R"):
            cum += D.GACHA_RATES[rar]
            if r < cum:
                return rar
        return "R"

    def pull_one(self, banner, pull_index_in_batch):
        """Roll one hero from a banner. Returns (hero_id, rarity, is_featured).
        The SR+ guarantee fires on every Nth pull since the last SR+ (cumulative
        per-banner), so it works for single pulls + any batch size, not just 10s.
        """
        bid = banner["id"]
        pity = self.pity(bid)
        self._set_pity(bid, pity + 1)
        pity = self.pity(bid)

        # hard pity -> guaranteed SSR
        if pity >= self.PITY_HARD:
            rarity = "SSR"
        else:
            rarity = self._roll_rarity(banner)
            # soft pity ramp: after SOFT_PITY pulls, SSR chance climbs — but cap
            # below 100% so the hard pity (60) stays the real, honest guarantee
            if rarity != "SSR" and pity >= self.SOFT_PITY:
                # smooth ramp capped at 0.9; hard pity is the true floor
                ramp = min(0.9, (pity - self.SOFT_PITY + 1) * 0.08)
                if random.random() < ramp:
                    rarity = "SSR"
            # SR+ guarantee: every Nth pull since the last SR+ is at least SR.
            # Tracked cumulatively per banner so single pulls + non-10 batches
            # are covered (not just the 10th of a 10-pull).
            sr_counter = self.player.gacha_pity.get(bid + "_sr", 0) + 1
            self.player.gacha_pity[bid + "_sr"] = sr_counter
            if rarity == "R" and sr_counter >= self.SR_GUARANTEE_EVERY:
                rarity = self._roll_rarity(banner, force_sr_floor=True)
            if rarity in ("SSR", "SR"):
                # reset the SR+ counter whenever we hit SR or better
                self.player.gacha_pity[bid + "_sr"] = 0

        if rarity == "SSR":
            self._set_pity(bid, 0)

        # pick the hero within the rarity, applying rate-up — exclude the
        # featured hero from the fallback pool so the split is an honest 50/50
        feat_ssr = banner.get("featured_ssr")
        feat_sr = banner.get("featured_sr")
        if rarity == "SSR" and feat_ssr and feat_ssr in banner["pool"]["SSR"]:
            others = [h for h in banner["pool"]["SSR"] if h != feat_ssr]
            hero_id = feat_ssr if (random.random() < 0.5 or not others) else random.choice(others)
        elif rarity == "SR" and feat_sr and feat_sr in banner["pool"]["SR"]:
            others = [h for h in banner["pool"]["SR"] if h != feat_sr]
            hero_id = feat_sr if (random.random() < 0.5 or not others) else random.choice(others)
        else:
            hero_id = random.choice(banner["pool"][rarity])

        is_featured = (rarity == "SSR" and hero_id == feat_ssr) or \
                      (rarity == "SR" and hero_id == feat_sr)
        return hero_id, rarity, is_featured

    def pull(self, banner_id, count):
        """Run `count` pulls on a banner. Returns a list of
        (hero_id, rarity, is_featured) tuples."""
        banner = self.banner(banner_id)
        results = []
        for i in range(count):
            results.append(self.pull_one(banner, i))
        return results

    def apply_result(self, hero_id, rarity, is_featured):
        """Add a pulled hero to the player; return (status, refund_gems).
        status: 'new' | 'dupe'. Maxed dupes refund a few gems."""
        status = "new"
        refund = 0
        if hero_id in self.player.owned:
            status = "dupe"
            rec = self.player.owned[hero_id]
            if rec.get("ascension", 0) >= D.MAX_ASCENSION:
                # already maxed -> refund some gems instead of more shards
                refund = D.GACHA_DUPE_GEM_REFUND
                self.player.gems += refund
                self.player.stats["gems_earned"] = self.player.stats.get("gems_earned", 0) + refund
            else:
                rec["ascension"] = rec.get("ascension", 0) + 1
                rec["dupes"] = rec.get("dupes", 0) + 1
        else:
            self.player.add_hero(hero_id)
        return status, refund

    def pity_to_hard(self, banner_id):
        """Pulls remaining until the hard-pity SSR (for the pity meter UI)."""
        return max(0, self.PITY_HARD - self.pity(banner_id))
