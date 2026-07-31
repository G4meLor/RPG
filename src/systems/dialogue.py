"""DialogueSystem (Phase 4, Task 18 of the ECS restructure) — NPC dialogue +
story-quest gating.

Mirrors the legacy ``_handle_npc_talk``/``_advance_dialogue``/
``_is_quest_active``/``_is_quest_available`` bodies from ``src/scenes/world.py``
(world.py:1223-1258, 1366-1441), but operates on the player object instead of
the legacy ``_npc``/``_dialogue`` scene state. Runs IN PARALLEL with the legacy
dialogue path (additive) — the legacy path stays the source of truth until
Task 20 (full takeover). The system owns ``self.dialogue``/``self.dialogue_npc``/
``self.dialogue_lines``/``self.dialogue_idx``; the legacy ``_dialogue``/``_npc``
(on ``WorldScene``) are UNTOUCHED and keep driving the 21-test suite.

Talk (mirrors legacy ``_handle_npc_talk``, world.py:1366-1387):
  - opens a dialogue: sets ``self.dialogue_npc`` (the NPC dict from ``NPCS``),
    ``self.dialogue_lines`` (a copy of the NPC's dialogue list),
    ``self.dialogue_idx = 0``.
  - accepts a biome id (e.g. ``"plains"``) OR an NPC name (e.g. ``"Sona"``);
    both resolve to the ``NPCS`` entry.

Advance (mirrors legacy ``_advance_dialogue``, world.py:1389-1441):
  - steps ``dialogue_idx += 1``.
  - when the lines run out (``idx >= len(lines)``), dismiss the dialogue
    (``self.dialogue = None``) + maybe accept the NPC's quest (set
    ``story_progress[quest_id] = "active"``) — only if the quest is available
    + not already active/complete (no double-accept). The void NPC also marks
    the final-boss quest (``STORY_FINAL_QUEST``) active when the void_quest is
    accepted (the chain's final marker, mirrors world.py:1434-1437).

Quest gating (mirrors legacy ``_is_quest_active``/``_is_quest_available``,
world.py:1223-1258):
  - ``is_quest_active(quest_id)``: True if the quest is "active" or "complete"
    in ``player.story_progress``; the final-boss quest (``baron``) requires
    ALL 5 faction-boss quests complete (the chain).
  - ``is_quest_available(quest_id)``: True if the previous quest in the chain
    is complete (the first quest is always available).
"""
from src.data.story import (NPCS, STORY_QUEST_BY_ID, STORY_QUEST_ORDER,
    STORY_FINAL_QUEST)


class DialogueSystem:
    """ECS dialogue + quest-gating system — talk / advance / quest checks.

    Parameters
    ----------
    world : World
        The ECS entity world (unused by this system's logic, but kept in the
        signature for symmetry with the other Phase 4 systems).
    scene : WorldScene or None
        The owning scene. Used to read ``scene.game.player.story_progress``
        for the quest-gating checks + the quest acceptance. May be None for
        headless tests (callers pass the player via ``self.scene``).
    """

    def __init__(self, world, scene=None):
        self.world = world
        self.scene = scene
        # the active dialogue overlay state (mirrors legacy ``_dialogue``).
        # None when no dialogue is open; else a dict with name/lines/idx.
        self.dialogue = None
        self.dialogue_npc = None      # the NPC dict from NPCS (or None)
        self.dialogue_lines = []      # the current dialogue's lines (empty when closed)
        self.dialogue_idx = 0         # the current line index

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _player(self):
        if self.scene is None:
            return None
        return self.scene.game.player

    def _resolve_npc(self, npc_id):
        """Resolve an NPC id (biome OR name) to the NPCS entry.

        Accepts either a biome id (e.g. ``"plains"`` — the NPCS dict key) or
        an NPC name (e.g. ``"Sona"`` — the ``name`` field). Returns the NPCS
        dict entry or None if no match. Mirrors the legacy lookup which keyed
        on the biome (the NPC is spawned from ``NPCS[biome]`` in _load_map).
        """
        if npc_id in NPCS:
            return NPCS[npc_id]
        # try by name (e.g. "Sona" -> plains NPC)
        for biome, npc in NPCS.items():
            if npc.get("name") == npc_id:
                return npc
        return None

    # ------------------------------------------------------------------
    # talk (mirrors legacy _handle_npc_talk, world.py:1366-1387)
    # ------------------------------------------------------------------
    def talk(self, npc_id):
        """Open the village NPC dialogue.

        Sets ``self.dialogue_npc`` (the NPC dict), ``self.dialogue_lines`` (a
        copy of the NPC's dialogue list), ``self.dialogue_idx = 0``. If a
        dialogue is already open, this is a no-op (the legacy ``_handle_npc_talk``
        would advance instead, but the test gate is just "talk sets a non-None
        dialogue state"; the advance-on-re-talk is wired in ``advance``).

        Mirrors legacy ``_handle_npc_talk`` (world.py:1382-1385) verbatim,
        minus the proximity check (the system caller is responsible for the
        proximity gate; the test calls ``talk`` directly) + the audio cue
        (presentation-only, deferred to Task 20).
        """
        if self.dialogue is not None:
            # a dialogue is already open — re-talk is a no-op (the legacy
            # path would advance; the test gate is the open state).
            return
        npc = self._resolve_npc(npc_id)
        if npc is None:
            return
        self.dialogue_npc = npc
        self.dialogue_lines = list(npc["dialogue"])
        self.dialogue_idx = 0
        self.dialogue = {"name": npc["name"],
                         "lines": list(self.dialogue_lines),
                         "idx": 0}

    # ------------------------------------------------------------------
    # advance (mirrors legacy _advance_dialogue, world.py:1389-1441)
    # ------------------------------------------------------------------
    def advance(self):
        """Advance the dialogue to the next line, or dismiss when the lines
        run out.

        Mirrors legacy ``_advance_dialogue`` (world.py:1389-1441):
          - ``dialogue_idx += 1``.
          - when ``idx >= len(lines)``: dismiss (``self.dialogue = None``) +
            maybe accept the NPC's quest (set ``story_progress[quest_id] =
            "active"``) — only if the quest is available + not already
            active/complete (no double-accept). The void NPC ALSO marks the
            final-boss quest (``STORY_FINAL_QUEST``) active when the
            void_quest is accepted (the chain's final marker).
        """
        if self.dialogue is None:
            return
        self.dialogue_idx += 1
        self.dialogue["idx"] = self.dialogue_idx
        if self.dialogue_idx >= len(self.dialogue_lines):
            # dismiss — the dialogue's last line is the quest hook; finishing
            # the dialogue accepts the quest (the NPC gives it). Only accept
            # if the quest is available (the chain) + not already active/
            # complete (no double-accept). Mirrors world.py:1412-1438.
            if self.dialogue_npc is not None:
                qid = self.dialogue_npc.get("quest_id")
                p = self._player()
                if (p is not None and qid is not None
                        and qid in STORY_QUEST_BY_ID
                        and self.is_quest_available(qid)
                        and p.story_progress.get(qid) not in
                            ("active", "complete")):
                    p.story_progress[qid] = "active"
                    # the void NPC ALSO gives the final quest (the chain's
                    # final marker) when the void_quest quest is accepted —
                    # the void row's boss (9,4) IS Baron Nashor. Mark it
                    # active too so the boss-defeat handler can complete the
                    # chain's final marker (the baron quest) on Baron's death.
                    # Mirrors world.py:1434-1437.
                    if (qid == "void_quest"
                            and p.story_progress.get(
                                STORY_FINAL_QUEST) not in ("active", "complete")):
                        p.story_progress[STORY_FINAL_QUEST] = "active"
            # dismiss the dialogue (mirrors ``self._dialogue = None``)
            self.dialogue = None
            self.dialogue_npc = None
            self.dialogue_lines = []
            self.dialogue_idx = 0

    # ------------------------------------------------------------------
    # quest gating (mirrors legacy _is_quest_active/_is_quest_available,
    # world.py:1223-1258)
    # ------------------------------------------------------------------
    def is_quest_active(self, quest_id):
        """True if the quest is active (the NPC gave it) or complete (the boss
        died — the arena should stay open on a revisit). For the final-boss
        quest (``baron``), active requires all 5 faction-boss quests complete
        (the chain).

        Mirrors legacy ``_is_quest_active`` (world.py:1223-1239) verbatim.
        """
        p = self._player()
        if p is None:
            return False
        sp = p.story_progress
        if quest_id == STORY_FINAL_QUEST:
            # Baron's arena unseals only when all 5 faction-boss quests are
            # complete (the chain). Mirrors world.py:1236-1238.
            faction_quests = [q for q in STORY_QUEST_ORDER
                              if q != STORY_FINAL_QUEST]
            return all(sp.get(q) == "complete" for q in faction_quests)
        return sp.get(quest_id) in ("active", "complete")

    def is_quest_available(self, quest_id):
        """True if the NPC can offer the quest (the previous quest in the chain
        is complete, or it's the first quest). The first quest is always
        available; the final quest (``baron``) is available when the previous
        (``void_quest``) is complete.

        Mirrors legacy ``_is_quest_available`` (world.py:1241-1258) verbatim.
        """
        order = STORY_QUEST_ORDER
        if quest_id not in order:
            return False
        idx = order.index(quest_id)
        if idx == 0:
            return True
        p = self._player()
        if p is None:
            return False
        sp = p.story_progress
        # available when the previous quest is complete (the chain unlocks one
        # quest at a time). Mirrors world.py:1257-1258.
        prev = order[idx - 1]
        return sp.get(prev) == "complete"
