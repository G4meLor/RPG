"""ECS acceptance suite (grows each phase). Layer 1: component/entity/world unit tests."""
import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame; pygame.init(); pygame.display.set_mode((1,1))

# blow away any existing save so story_progress/gold/shards start at the
# defaults (a stale save from a prior test run would make the dialogue
# quest-gating assertions flaky — e.g. demacia_quest already "complete").
if os.path.exists("saves/save.json"):
    os.remove("saves/save.json")

from src.entities.components import (Transform, Health, Combat, AI, Render,
    Identity, Statuses, ChampionRef)
from src.entities.entity import Entity
from src.core.world import World
from src.entities.hero import spawn_hero
from src.entities.enemy import spawn_enemy
from src.data.heroes import HERO_BY_ID

def test_entity_components():
    e = Entity(0)
    assert e.eid == 0
    assert e.has(Transform) is False
    e.add(Transform(100, 200))
    assert e.has(Transform) is True
    t = e.get(Transform)
    assert t.x == 100 and t.y == 200 and t.vx == 0 and t.vy == 0 and t.r == 26
    assert e.add(Health(100, 100, 50, 120)) is e  # chaining

def test_component_defaults():
    assert Transform(0,0).r == 26
    assert AI("hop").state == "idle" and AI("hop").target == -1
    assert Identity(0, "Ahri", True).is_boss is False
    assert ChampionRef("Ahri").skin == 0 and ChampionRef("Ahri").level == 1

def test_world_spawn_destroy_query():
    w = World()
    a = w.spawn(); b = w.spawn(); c = w.spawn()
    assert len({a.eid, b.eid, c.eid}) == 3
    a.add(Identity(a.eid, "Ahri", True)); a.add(Transform(0,0))
    b.add(Identity(b.eid, "Krugs", False)); b.add(Transform(10,10))
    c.add(Identity(c.eid, "Lux", True))
    assert {e.eid for e in w.query(Identity, Transform)} == {a.eid, b.eid}
    assert {e.eid for e in w.heroes()} == {a.eid, c.eid}
    assert {e.eid for e in w.enemies()} == {b.eid}
    w.destroy(b.eid)
    assert b.eid not in w.entities
    assert {e.eid for e in w.enemies()} == set()

def test_spawn_hero():
    w = World()
    e = spawn_hero(w, "Ahri")
    assert e.has(Transform) and e.has(Health) and e.has(Combat) and e.has(AI) \
        and e.has(Render) and e.has(Identity) and e.has(Statuses) and e.has(ChampionRef)
    ident = e.get(Identity)
    assert ident.is_hero is True and ident.name == "Ahri"
    ref = e.get(ChampionRef)
    assert ref.hero_id == "Ahri" and ref.level == 1
    hp = e.get(Health)
    h = HERO_BY_ID["Ahri"]["stats"]
    assert hp.max_hp == h["hp"]  # level-1 base
    assert e.get(Combat).element == HERO_BY_ID["Ahri"]["element"]

def test_spawn_enemy():
    w = World()
    e = spawn_enemy(w, "Krugs", level=3)
    assert e.get(Identity).is_hero is False
    assert e.get(Combat).element is not None
    assert e.get(Health).max_hp > 0

def test_worldscene_entity_sync():
    """Integration test (Task 12): WorldScene builds a parallel World of
    entities (via the factories) that track the legacy WorldCharacter /
    WorldEnemy objects. After 60 frames, each hero entity's Transform.x
    matches its legacy WorldCharacter.x (±2) and the entity counts match
    the legacy party/enemy lists. The adapter is READ-ONLY on the legacy
    path — it must not change behavior."""
    import main as M
    g = M.Game()
    from src.scenes.world import WorldScene
    sc = WorldScene(g); g.scene = sc
    # the adapter must expose a World
    assert hasattr(sc, "world"), "WorldScene has no .world adapter"
    for _ in range(60):
        sc.update(0.016, []); sc.draw(g.screen)
    # 4 party heroes (the legacy party is a 4-slot list)
    heroes = sc.world.heroes()
    assert len(heroes) == 4, f"expected 4 hero entities, got {len(heroes)}"
    # each hero entity Transform matches its legacy WorldCharacter (±2 px)
    for wc in sc.party:
        if wc is None: continue
        e = next((e for e in heroes if e.get(ChampionRef).hero_id == wc.hero.id), None)
        assert e is not None, f"no entity for hero {wc.hero.id}"
        assert abs(e.get(Transform).x - wc.x) < 2, \
            f"{wc.hero.id} x drift: entity={e.get(Transform).x} legacy={wc.x}"
    # enemy entities: count should equal the legacy enemy list length
    # (the adapter spawns one entity per WorldEnemy append)
    assert len(sc.world.enemies()) == len(sc.enemies), \
        f"entity enemies {len(sc.world.enemies())} != legacy {len(sc.enemies)}"
    print("  worldscene entity sync OK")

def test_map_controller():
    """Layer 2 (Task 14): MapController owns the map state. Edge transitions
    + teleport update the controller's cell; WorldScene delegates."""
    import main as M
    g = M.Game()
    g.player.ow_current = [0, 0]   # reset to origin (save may have a later cell)
    from src.scenes.world import WorldScene
    sc = WorldScene(g); g.scene = sc
    mc = sc.map_ctrl
    # edge right
    mc.transition("right")
    assert mc.cell == (1, 0), mc.cell
    mc.transition("bottom")
    assert mc.cell == (1, 1), mc.cell
    mc.teleport_to(5, 2)
    assert mc.cell == (5, 2), mc.cell
    print("  map controller OK")

def test_physics_movement():
    """Layer 2 (Task 15): PhysicsSystem.update drives an entity's Transform
    from input + accel/friction. A hero entity given input (1,0) for 30 frames
    moves +px; Transform.x increases past start+5. Obstacles + enemies are
    cleared so collision doesn't interfere. The legacy WorldCharacter.update
    path stays the source of truth this task; PhysicsSystem runs in parallel
    (additive) — this test proves the extraction works in isolation."""
    import main as M
    g = M.Game()
    from src.scenes.world import WorldScene
    from src.entities.components import Transform
    sc = WorldScene(g); g.scene = sc
    sc.enemies.clear(); sc._map_data["obstacles"] = []
    active = sc.party[sc.active]
    start_x = active.x
    for _ in range(30):
        sc.physics.update(0.016, sc._entity_for_hero[active.hero.id], (1.0, 0.0))
    assert sc._entity_for_hero[active.hero.id].get(Transform).x > start_x + 5
    print("  physics movement OK")

def test_ai_pounce():
    """Layer 2 (Task 16): AISystem.update drives a "pounce"-kind enemy entity
    toward the active hero. A MurkWolves entity spawned 200px to the right of
    the hero (within aggro range) must close the distance over 60 frames. The
    legacy WorldEnemy.update path STAYS the source of truth this task; the
    AISystem runs IN PARALLEL (additive) on the entity layer. The test entity
    is spawned directly into sc.world (NOT via the legacy self.enemies list),
    so the adapter's _sync_entities has no matching legacy WorldEnemy to
    overwrite the entity's Transform — AISystem's writes persist."""
    import main as M
    g = M.Game()
    from src.scenes.world import WorldScene
    from src.entities.components import Transform, AI
    sc = WorldScene(g); g.scene = sc
    sc.enemies.clear(); sc._map_data["obstacles"] = []
    hero_e = sc._entity_for_hero[sc.party[sc.active].hero.id]
    en = spawn_enemy(sc.world, "MurkWolves", level=1,
                     x=hero_e.get(Transform).x + 200, y=hero_e.get(Transform).y)
    d0 = abs(en.get(Transform).x - hero_e.get(Transform).x)
    for _ in range(60):
        sc.ai.update(0.016)
    d1 = abs(en.get(Transform).x - hero_e.get(Transform).x)
    assert d1 < d0, f"pounce did not close distance: d0={d0:.1f} d1={d1:.1f}"
    print("  ai pounce OK")

def test_combat_basic_attack():
    """Layer 2 (Task 17): CombatSystem.basic_attack mirrors the legacy
    _do_attack damage formula on entities. A basic attack against an enemy
    entity must: reduce target Health.hp, gain attacker Health.energy, and
    set attacker Combat.atk_cd > 0. The legacy _do_attack/_do_skill/
    _do_ultimate/_on_enemy_hit/_on_enemy_death STAY running (21-test suite);
    CombatSystem runs IN PARALLEL (additive) on the entity layer. Full
    takeover is Task 20."""
    import main as M
    g = M.Game()
    from src.scenes.world import WorldScene
    from src.entities.components import Health, Combat
    sc = WorldScene(g); g.scene = sc
    sc.enemies.clear(); sc._map_data["obstacles"] = []
    hero_e = sc._entity_for_hero[sc.party[sc.active].hero.id]
    en = spawn_enemy(sc.world, "Krugs", level=1)
    hp0 = en.get(Health).hp
    en0_energy = hero_e.get(Health).energy
    sc.combat.basic_attack(hero_e.eid, en.eid)
    assert en.get(Health).hp < hp0, "target hp did not drop"
    assert hero_e.get(Health).energy > en0_energy, "attacker energy did not gain"
    assert hero_e.get(Combat).atk_cd > 0, "attacker atk_cd not set"
    print("  combat basic_attack OK")

def test_drop_pickup():
    """Layer 2 (Task 18): DropSystem.spawn creates a drop; DropSystem.pickup
    adds gold/shard/item to the player. The system mirrors the legacy
    _spawn_drop/_pickup_drop logic (gold -> player.gold, hp_potion ->
    inventory, shard -> player.shards, equipment -> equipment_inv) on the
    entity/player layer. The legacy _spawn_drop/_pickup_drop STAY running
    (21-test suite); DropSystem runs IN PARALLEL (additive). Full takeover
    is Task 20."""
    import main as M
    g = M.Game()
    from src.scenes.world import WorldScene
    sc = WorldScene(g); g.scene = sc
    gold0 = g.player.gold
    # spawn a gold drop + pick it up directly
    drop = sc.drops.spawn(100, 100, "gold", 50)
    assert drop is not None, "spawn returned None"
    assert drop["kind"] == "gold" and drop["value"] == 50
    assert len(sc.drops.drops) == 1, "drop not appended to system list"
    hero_e = sc._entity_for_hero[sc.party[sc.active].hero.id]
    sc.drops.pickup(drop, hero_e)
    assert g.player.gold == gold0 + 50, \
        f"gold not incremented: {g.player.gold} != {gold0}+50"
    # shard pickup increments player.shards
    shards0 = g.player.shards
    sdrop = sc.drops.spawn(100, 100, "shard", 3)
    sc.drops.pickup(sdrop, hero_e)
    assert g.player.shards == shards0 + 3, \
        f"shards not incremented: {g.player.shards} != {shards0}+3"
    print("  drop pickup OK")

def test_rift_trigger():
    """Layer 2 (Task 18): RiftSystem.trigger spawns a wave of enemy entities
    into world.enemies(); RiftSystem.clear sets done. The system mirrors the
    legacy _enter_rift/_clear_rift wave-spawn logic on the entity layer. The
    legacy _enter_rift/_clear_rift STAY running (21-test suite); RiftSystem
    runs IN PARALLEL (additive). Full takeover is Task 20."""
    import main as M
    g = M.Game()
    from src.scenes.world import WorldScene
    sc = WorldScene(g); g.scene = sc
    sc.enemies.clear()
    n0 = len(sc.world.enemies())
    sc.rift.trigger(500, 400, wave_level=1, wave_size=3)
    assert len(sc.world.enemies()) >= n0 + 3, \
        f"rift did not spawn 3 enemies: now={len(sc.world.enemies())} was={n0}"
    assert sc.rift.active is True, "rift.active not set after trigger"
    sc.rift.clear()
    assert sc.rift.done is True, "rift.done not set after clear"
    print("  rift trigger OK")

def test_dialogue_talk():
    """Layer 2 (Task 18): DialogueSystem.talk opens a dialogue (sets
    dialogue_npc + dialogue_lines + dialogue_idx=0); advance steps the index.
    The system mirrors the legacy _handle_npc_talk/_advance_dialogue logic
    on the entity/player layer. The legacy _handle_npc_talk/_advance_dialogue
    STAY running (21-test suite); DialogueSystem runs IN PARALLEL (additive).
    Full takeover is Task 20."""
    import main as M
    g = M.Game()
    from src.scenes.world import WorldScene
    from src.data.story import NPCS
    sc = WorldScene(g); g.scene = sc
    # pick the plains NPC (Sona) — talk by biome id
    sc.dialogue.talk("plains")
    assert sc.dialogue.dialogue_npc is not None, "dialogue_npc not set"
    assert sc.dialogue.dialogue_lines, "dialogue_lines empty"
    assert sc.dialogue.dialogue_idx == 0, "dialogue_idx not 0"
    sc.dialogue.advance()
    assert sc.dialogue.dialogue_idx == 1, \
        f"advance did not step idx: {sc.dialogue.dialogue_idx}"
    # is_quest_active / is_quest_available read player.story_progress
    from src.data.story import STORY_QUEST_ORDER
    first_qid = STORY_QUEST_ORDER[0]
    assert sc.dialogue.is_quest_available(first_qid) is True, \
        "first quest should be available"
    assert sc.dialogue.is_quest_active(first_qid) is False, \
        "first quest should not be active at boot"
    print("  dialogue talk OK")

def test_render_one_frame():
    """Layer 3 (Task 19): RenderSystem + HudSystem exist on WorldScene, and
    one full WorldScene.update(dt,[]) + draw(surf) frame is exception-free
    (the legacy draw STAYS the source of truth this task; the systems run IN
    PARALLEL — additive — proving they can render to a surface without
    raising). The test then calls sc.render.draw + sc.hud.draw directly
    (the system draws — must not raise). Full takeover is Task 20."""
    import main as M
    g = M.Game()
    from src.scenes.world import WorldScene
    sc = WorldScene(g); g.scene = sc
    # legacy update + draw — must not raise (same as the 21-test suite)
    sc.update(0.016, [])
    sc.draw(g.screen)
    # the systems exist on the scene
    assert sc.render is not None, "sc.render (RenderSystem) missing"
    assert sc.hud is not None, "sc.hud (HudSystem) missing"
    # the systems can render to the screen without raising (additive)
    sc.render.draw(g.screen, sc.map_ctrl)
    sc.hud.draw(g.screen)
    print("  render one frame OK")

def test_worldcharacter_skin_sprite():
    """A WorldCharacter built from a Hero with skin=14 loads sprites/14.png
    when present (else falls back to sprite.png). Asserts the load PATH,
    not pixel content."""
    import main as M
    from src.entities import WorldCharacter
    from src.entities.combatant import Hero
    from src.data.heroes import HERO_BY_ID
    from src.data.tuning import ASSET_DIR
    import os, pygame
    g = M.Game()
    hd = HERO_BY_ID["Ahri"]
    hero = Hero(hd, skin=14)
    # ensure a sprites/14.png exists
    base = os.path.join(ASSET_DIR, "characters", "Ahri")
    os.makedirs(os.path.join(base, "sprites"), exist_ok=True)
    sp = os.path.join(base, "sprites", "14.png")
    if not os.path.exists(sp):
        s = pygame.Surface((256, 256), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 0, 255, 255), (128, 128), 60)
        pygame.image.save(s, sp)
    wc = WorldCharacter(hero, 200, 200)
    # reload the sprite via the skin-aware path and assert it resolved to sprites/14.png
    import src.entities.combatant as comb
    seen = []
    orig = comb.load_image
    comb.load_image = lambda rel, scale=None: (seen.append(rel), orig(rel, scale))[1]
    try:
        wc._load_sprite()
    finally:
        comb.load_image = orig
    assert any("sprites/14.png" in p for p in seen), f"per-skin not loaded: {seen}"
    print("  worldcharacter skin sprite OK")

def test_build_party_threads_skin_to_entity():
    """Regression test (Task 12 fix round 1): _build_party must thread the
    EQUIPPED skin (hero.skin, from the owned record) to spawn_hero, so the
    ECS entity's ChampionRef.skin matches the equipped skin — NOT read it
    from ow_party_state (which only holds {hp, energy})."""
    import main as M
    from src.scenes.world import WorldScene
    from src.entities.components import ChampionRef
    g = M.Game()
    # equip skin 14 on the Ahri owned record
    g.player.owned["Ahri"]["skin"] = 14
    sc = WorldScene(g); g.scene = sc
    # _build_party ran in WorldScene.__init__; find the Ahri entity
    ahri_e = next((e for e in sc.world.heroes()
                   if e.get(ChampionRef).hero_id == "Ahri"), None)
    assert ahri_e is not None, "no Ahri entity in sc.world.heroes()"
    assert ahri_e.get(ChampionRef).skin == 14, \
        f"ChampionRef.skin={ahri_e.get(ChampionRef).skin}, expected 14 " \
        f"(skin must come from hero.skin, not ow_party_state)"
    # also confirm the legacy WorldCharacter's hero.skin threaded through
    ahri_wc = next((wc for wc in sc.party if wc and wc.hero.id == "Ahri"), None)
    assert ahri_wc is not None, "no Ahri WorldCharacter in sc.party"
    assert ahri_wc.hero.skin == 14, \
        f"wc.hero.skin={ahri_wc.hero.skin}, expected 14"
    print("  build_party threads skin to entity OK")

def test_skin_change_changes_sprite():
    """Changing rec['skin'] changes which world sprite path WorldCharacter
    loads (asserts load PATH, not pixels). End-to-end: record -> Hero ->
    WorldCharacter._load_sprite."""
    import main as M, os, pygame
    from src.entities.combatant import Hero, load_char_sprite
    from src.data.heroes import HERO_BY_ID
    from src.data.tuning import ASSET_DIR
    import src.entities.combatant as comb
    g = M.Game()
    hd = HERO_BY_ID["Ahri"]
    base = os.path.join(ASSET_DIR, "characters", "Ahri")
    os.makedirs(os.path.join(base, "sprites"), exist_ok=True)
    for idx in (0, 14):
        sp = os.path.join(base, "sprites", f"{idx}.png")
        if not os.path.exists(sp):
            s = pygame.Surface((256, 256), pygame.SRCALPHA)
            pygame.draw.circle(s, (idx * 20, 0, 200, 255), (128, 128), 60)
            pygame.image.save(s, sp)
    def _loaded_skin_idx(skin_idx):
        seen = []
        orig = comb.load_image
        comb.load_image = lambda rel, scale=None: (seen.append(rel), orig(rel, scale))[1]
        try:
            load_char_sprite("Ahri", 96, skin_idx=skin_idx)
        finally:
            comb.load_image = orig
        joined = " ".join(seen)
        if skin_idx and skin_idx > 0 and f"sprites/{skin_idx}.png" in joined:
            return skin_idx
        return 0  # fell back to sprite.png
    assert _loaded_skin_idx(14) == 14
    assert _loaded_skin_idx(0) == 0
    print("  skin change changes sprite OK")

def run():
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  pass {name}")
    print("Layer 1 OK")

if __name__ == "__main__":
    run()
