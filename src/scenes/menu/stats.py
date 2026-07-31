"""Stats scene."""
import pygame

from src.core.scene import Scene
from src.ui import (WIDTH, HEIGHT, WHITE, DIM, GOLD, BG_DARK, Button, draw_panel,
                    draw_bar, text, f)
from src.data.progression import ACHIEVEMENTS, DAILY_QUESTS
from src.data.story import STORY_QUESTS, STORY_QUEST_BY_ID, STORY_QUEST_ORDER
import src.audio as audio
class StatsScene(Scene):
    """Show battle stats, achievements, the story chain, and daily quests."""
    def __init__(self, game):
        super().__init__(game)
        self.back_btn = Button((40, 40, 140, 48), "Back", (60, 60, 90), (90, 90, 130), size=20)
        self.tab = "stats"
        self.tab_stats = Button((WIDTH // 2 - 320, 100, 120, 44), "Stats", (60, 80, 120), (90, 120, 180), size=18)
        self.tab_ach = Button((WIDTH // 2 - 190, 100, 120, 44), "Awards", (60, 80, 120), (90, 120, 180), size=18)
        self.tab_story = Button((WIDTH // 2 - 60, 100, 120, 44), "Story", (60, 80, 120), (90, 120, 180), size=18)
        self.tab_quest = Button((WIDTH // 2 + 70, 100, 150, 44), "Daily Quests", (60, 80, 120), (90, 120, 180), size=14)
        # "Claim All" button for the Daily Quests tab (reduces the daily chore
        # from one click per quest to one click for the whole board).
        self.claim_all_btn = Button((WIDTH // 2 - 110, 158, 220, 34), "Claim All",
                                    (90, 160, 110), (120, 200, 130), size=16)
        self.scroll = 0
        self.quest_rects = []
        self.t = 0
        # reward toast (shown after claiming a quest or the whole board)
        self.toast = ""
        self.toast_t = 0

    def update(self, dt, events):
        self.t += dt
        if self.toast_t > 0:
            self.toast_t -= dt
        mp = pygame.mouse.get_pos()
        mdown = pygame.mouse.get_pressed()[0]
        self.back_btn.update(mp, mdown)
        self.tab_stats.update(mp, mdown)
        self.tab_ach.update(mp, mdown)
        self.tab_story.update(mp, mdown)
        self.tab_quest.update(mp, mdown)
        self.claim_all_btn.update(mp, mdown)
        self.game.player.reset_quests_if_needed()
        self.quest_rects = []
        for i, qid in enumerate(DAILY_QUESTS):
            r = pygame.Rect(WIDTH // 2 - 280, 200 + i * 80, 560, 70)
            self.quest_rects.append((qid, r))
        for e in events:
            if self.back_btn.clicked(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                self.game.back("title")
                return
            if self.tab_stats.clicked(e):
                self.tab = "stats"; self.scroll = 0
            if self.tab_ach.clicked(e):
                self.tab = "ach"; self.scroll = 0
            if self.tab_story.clicked(e):
                self.tab = "story"; self.scroll = 0
            if self.tab_quest.clicked(e):
                self.tab = "quest"; self.scroll = 0
            # keyboard tab switching (Left/Right arrows) for consistency with the
            # world scene's full keyboard control.
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_LEFT, pygame.K_RIGHT):
                order = ["stats", "ach", "story", "quest"]
                idx = order.index(self.tab) if self.tab in order else 0
                if e.key == pygame.K_LEFT:
                    self.tab = order[max(0, idx - 1)]
                else:
                    self.tab = order[min(len(order) - 1, idx + 1)]
                self.scroll = 0
                audio.play("menu_click", 0.3)
                return
            if self.tab == "quest" and self.claim_all_btn.clicked(e):
                total = 0
                for qid in DAILY_QUESTS:
                    if self.game.player.claim_quest(qid):
                        total += DAILY_QUESTS[qid]["reward_gems"]
                if total > 0:
                    self.toast = f"Claimed all: +{total} gems!"
                    self.toast_t = 2.0
                    audio.play("menu_click", 0.5)
                return
            if self.tab == "quest" and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for qid, r in self.quest_rects:
                    if r.collidepoint(e.pos):
                        if self.game.player.claim_quest(qid):
                            q = DAILY_QUESTS[qid]
                            self.toast = f"+{q['reward_gems']} gems!"
                            self.toast_t = 1.6
                            audio.play("menu_click", 0.4)
                        return
            if e.type == pygame.MOUSEWHEEL:
                # clamp scroll to the active tab's content height so the list
                # can't scroll past its end (which left a blank screen).
                if self.tab == "stats":
                    content_h = 10 * 60
                elif self.tab == "ach":
                    content_h = len(ACHIEVEMENTS) * 72
                elif self.tab == "story":
                    content_h = len(STORY_QUESTS) * 80
                else:
                    content_h = len(DAILY_QUESTS) * 80
                max_scroll = max(0, content_h - (HEIGHT - 180 - 40))
                self.scroll = max(0, min(self.scroll - e.y * 40, max_scroll))

    def draw(self, surf):
        surf.fill(BG_DARK)
        text(surf, "Records", 40, WHITE, (WIDTH // 2, 40), center=True)
        # tab indicator
        for btn, key in [(self.tab_stats, "stats"), (self.tab_ach, "ach"),
                         (self.tab_story, "story"), (self.tab_quest, "quest")]:
            btn.color = (90, 120, 180) if self.tab == key else (60, 80, 120)
            btn.draw(surf)
        p = self.game.player
        if self.tab == "stats":
            rows = [
                ("Enemies Defeated", p.stats.get("enemies_defeated", 0)),
                ("Bosses Defeated", p.stats.get("bosses_defeated", 0)),
                ("Maps Discovered", len(p.ow_discovered)),
                ("Total Pulls", p.stats.get("total_pulls", 0)),
                ("Gold Earned", p.stats.get("gold_earned", 0)),
                ("Gems Earned", p.stats.get("gems_earned", 0)),
                ("Soul Shards", p.shards),
                ("Heroes Owned", len(p.owned)),
                ("Daily Clears", p.stats.get("daily_clears", 0)),
                ("Login Streak", p.login_streak),
            ]
            y = 180 - self.scroll
            for label, val in rows:
                draw_panel(surf, (WIDTH // 2 - 280, y, 560, 48))
                text(surf, label, 22, WHITE, (WIDTH // 2 - 260, y + 12))
                text(surf, str(val), 22, GOLD, (WIDTH // 2 + 240, y + 12))
                y += 60
        elif self.tab == "ach":
            y = 180 - self.scroll
            for aid, ach in ACHIEVEMENTS.items():
                unlocked = aid in p.achievements
                draw_panel(surf, (WIDTH // 2 - 300, y, 600, 64))
                text(surf, ach["name"], 22, GOLD if unlocked else WHITE, (WIDTH // 2 - 280, y + 8))
                text(surf, ach["desc"], 16, DIM, (WIDTH // 2 - 280, y + 34))
                text(surf, f"+{ach['reward_gems']} gems", 18,
                     (120, 200, 255) if unlocked else (120, 100, 100),
                     (WIDTH // 2 + 260, y + 20))
                if unlocked:
                    text(surf, "DONE", 16, (140, 220, 160), (WIDTH // 2 + 260, y + 40), center=True)
                y += 72
        elif self.tab == "story":
            # Story chain (Task E3) — the 6 STORY_QUESTS with complete/active/
            # locked state. The chain unlocks one quest at a time: a quest is
            # "complete" when its boss is dead, "active" when the NPC gave it,
            # "locked" when the previous quest isn't complete yet. The first
            # quest (plains_boss) is available from the start, so at boot only
            # the first is active/locked and the rest are locked. Read the
            # chain state from player.story_progress (quest_id -> status).
            y = 180 - self.scroll
            sp = p.story_progress
            for i, qid in enumerate(STORY_QUEST_ORDER):
                q = STORY_QUEST_BY_ID[qid]
                status = sp.get(qid)
                if status == "complete":
                    label = "COMPLETE"
                    col = (140, 220, 160)
                    mark = "v"
                elif status == "active":
                    label = "ACTIVE"
                    col = (255, 200, 80)
                    mark = ">"
                else:
                    label = "LOCKED"
                    col = (120, 120, 140)
                    mark = "X"
                r = pygame.Rect(WIDTH // 2 - 300, y, 600, 64)
                draw_panel(surf, r)
                # status mark (check/triangle/lock) on the left
                text(surf, mark, 22, col, (r.x + 16, r.y + 8))
                text(surf, q["name"], 22, WHITE if status != "locked" else DIM,
                     (r.x + 56, r.y + 8))
                text(surf, q["objective"], 14, DIM, (r.x + 56, r.y + 34))
                text(surf, label, 16, col, (r.right - 16, r.y + 22), center=False)
                # the reward line (gems + shards) so the player sees the payout
                rw = q.get("reward", {})
                rtxt = f"+{rw.get('gems', 0)} gems  +{rw.get('shards', 0)} shards"
                text(surf, rtxt, 14, (120, 200, 255), (r.right - 16, r.y + 42), center=False)
                y += 80
        else:  # quest
            self.claim_all_btn.draw(surf)
            for qid, r in self.quest_rects:
                q = DAILY_QUESTS[qid]
                st = p.quests.get(qid, dict(progress=0, claimed=False, goal=q["goal"]))
                prog = st.get("progress", 0)
                goal = st.get("goal", q["goal"])
                claimed = st.get("claimed", False)
                done = prog >= goal
                draw_panel(surf, r)
                text(surf, q["name"], 20, WHITE, (r.x + 16, r.y + 8))
                text(surf, q["desc"], 14, DIM, (r.x + 16, r.y + 32))
                draw_bar(surf, (r.x + 16, r.y + 50, 360, 12), prog / max(1, goal), (120, 200, 255))
                text(surf, f"{prog}/{goal}", 16, WHITE, (r.x + 390, r.y + 44))
                mp = pygame.mouse.get_pos()
                claim_rect = pygame.Rect(r.right - 120, r.y + 20, 100, 34)
                if done and not claimed:
                    col = (90, 160, 110) if claim_rect.collidepoint(mp) else (60, 120, 80)
                    pygame.draw.rect(surf, col, claim_rect, border_radius=8)
                    text(surf, "Claim", 16, WHITE, claim_rect.center, center=True)
                elif claimed:
                    text(surf, "Claimed", 16, (140, 220, 160), claim_rect.center, center=True)
        # reward toast (claim feedback)
        if self.toast_t > 0:
            draw_panel(surf, (WIDTH // 2 - 150, HEIGHT - 80, 300, 48))
            text(surf, self.toast, 22, (120, 200, 255), (WIDTH // 2, HEIGHT - 56), center=True)
        self.back_btn.draw(surf)


# ---------------------------------------------------------------------------
# Codex scene
# ---------------------------------------------------------------------------
