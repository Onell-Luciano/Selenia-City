Congratulations! Your final score is 350595

import sys
import math

# --- Bot heuristique pour "Selenia City" puzzle ---
# - Greedy: connecte chaque nouvelle aire d'atterrissage à un module du type voulu
#   en privilégiant tubes droits non-croisés; sinon pose un téléporteur si possible.
# - Crée des pods navette simples sur les tubes existants.
# - Garde l'état entre les mois (bâtiments, tubes, téléporteurs, pods).
#
# Note: conçu pour être simple, rapide (<500ms) et stable. Améliorations possibles :
# - chercher chemins multi-segments entre bâtiments,
# - upgrade de tubes, logique avancée de pods et équilibrage plus fin.

# --- Helpers géométriques (d'après l'énoncé) ---
EPS = 1e-7

def dist(a, b):
    return math.hypot(a['x'] - b['x'], a['y'] - b['y'])

def point_on_segment(A, B, C):
    # vérifie si C est sur le segment AB
    return abs(dist(B, A) + dist(A, C) - dist(B, C)) < EPS

def orientation(p1, p2, p3):
    prod = (p3['y'] - p1['y']) * (p2['x'] - p1['x']) - (p2['y'] - p1['y']) * (p3['x'] - p1['x'])
    if abs(prod) < EPS:
        return 0
    return 1 if prod > 0 else -1

def segments_intersect(A, B, C, D):
    # True si les segments AB et CD se croisent en dehors des extrémités
    o1 = orientation(A, B, C)
    o2 = orientation(A, B, D)
    o3 = orientation(C, D, A)
    o4 = orientation(C, D, B)
    return o1 * o2 < 0 and o3 * o4 < 0

# --- State kept across months ---
buildings = {}        # id -> {'type': 'module'/'landing', 'moduleType': int or None, 'x': float, 'y': float, 'landing': [astronaut types]}
tubes = []            # list of (a_id, b_id, capacity)
teleports = set()     # set of frozenset({a,b}) where capacity==0 (teleport)
pods = {}             # pod_id -> [route list]
pod_id_counter = 1    # next pod id to try (1..500)
expected_occupancy = {}  # module_id -> estimated number of installed astronauts (for balancing)

# utilitaires rapides
def building_exists(bid):
    return bid in buildings

def tube_degree(bid):
    # nombre de tubes connectant ce bâtiment (tubes only)
    c = 0
    for a,b,_ in tubes:
        if a == bid or b == bid:
            c += 1
    return c

def any_building_on_segment(a_id, b_id):
    A = buildings[a_id]
    B = buildings[b_id]
    for cid, C in buildings.items():
        if cid == a_id or cid == b_id:
            continue
        if point_on_segment(A, B, C):
            return True
    return False

def crosses_existing_tube(a_id, b_id):
    A = buildings[a_id]
    B = buildings[b_id]
    for x,y,_ in tubes:
        # skip sharing endpoints (sharing at endpoints is allowed)
        if x in (a_id, b_id) or y in (a_id, b_id):
            continue
        C = buildings[x]
        D = buildings[y]
        if segments_intersect(A,B,C,D):
            return True
    return False

def can_build_tube(a_id, b_id):
    # conditions: neither building degree >=5, no other building on segment, no crossing
    if tube_degree(a_id) >= 5 or tube_degree(b_id) >= 5:
        return False
    if any_building_on_segment(a_id, b_id):
        return False
    if crosses_existing_tube(a_id, b_id):
        return False
    return True

def cost_tube(a_id, b_id):
    # 1 resource per 0.1 km, floor
    d = dist(buildings[a_id], buildings[b_id])
    return int(math.floor(d * 10.0 + 1e-9))

def have_teleport_endpoint(bid):
    # check if building already used as teleport endpoint
    for pair in teleports:
        if bid in pair:
            return True
    return False

def try_create_pod(route, resources, actions):
    # route: list of building ids; cost 1000. create if resources allow and pod id free
    global pod_id_counter
    # find next free id up to 500
    start_counter = pod_id_counter
    while pod_id_counter <= 500 and pod_id_counter in pods:
        pod_id_counter += 1
    if pod_id_counter > 500:
        # try to reuse some id (rare)
        for i in range(1,501):
            if i not in pods:
                pod_id_counter = i
                break
        else:
            return resources  # no id available
    if resources < 1000:
        return resources
    pid = pod_id_counter
    actions.append("POD " + " ".join(str(x) for x in ([pid] + route)))
    pods[pid] = list(route)
    resources -= 1000
    pod_id_counter += 1
    return resources

# --- Main game loop ---
first_turn = True
while True:
    try:
        resources = int(input())
    except Exception:
        # in case of EOF (debug runs), exit cleanly
        break
    num_travel_routes = int(input())
    # reset tubes/teleports for this turn, then rebuild from input (we keep our own state also)
    tubes = []
    teleports = set()
    for _ in range(num_travel_routes):
        a, b, capacity = [int(j) for j in input().split()]
        if capacity == 0:
            teleports.add(frozenset({a,b}))
        else:
            tubes.append((a,b,capacity))
    num_pods = int(input())
    pods_input = {}
    for _ in range(num_pods):
        parts = [int(x) for x in input().split()]
        if not parts:
            continue
        pid = parts[0]
        numStops = parts[1] if len(parts) > 1 else 0
        route = parts[2:2+numStops] if numStops > 0 else []
        pods_input[pid] = route
    # overwrite our pods state with simulator's known pods (keeps consistency)
    # but keep local pods dict for IDs that exist
    pods = {pid: route for pid, route in pods_input.items()}

    num_new_buildings = int(input())
    new_buildings_list = []
    for _ in range(num_new_buildings):
        vals = [int(x) for x in input().split()]
        if not vals:
            continue
        if vals[0] == 0:
            # landing: 0 buildingId coordX coordY numAstronauts astronautType1 astronautType2 ...
            _, buildingId, coordX, coordY, numAstronauts = vals[:5]
            astronaut_types = vals[5:5+numAstronauts]
            buildings[buildingId] = {'type': 'landing', 'moduleType': None, 'x': float(coordX), 'y': float(coordY), 'landing': astronaut_types}
            new_buildings_list.append(buildingId)
        else:
            # module: moduleType buildingId coordX coordY
            moduleType, buildingId, coordX, coordY = vals[:4]
            buildings[buildingId] = {'type': 'module', 'moduleType': moduleType, 'x': float(coordX), 'y': float(coordY), 'landing': []}
            expected_occupancy.setdefault(buildingId, 0)
            new_buildings_list.append(buildingId)

    # incorporate travel routes into state: ensure tubes/teleports reflect input (we already did)
    # Build auxiliary indices
    module_ids_by_type = {}
    for bid, info in buildings.items():
        if info['type'] == 'module':
            module_ids_by_type.setdefault(info['moduleType'], []).append(bid)

    # actions to produce this turn
    actions = []

    # Simple strategy:
    # 1) For each new landing, choose a target module of same type with minimal expected occupancy
    # 2) Try to connect by tube (direct); if impossible try teleporter; if still impossible, look for nearest intermediate building to connect to
    # 3) If a new tube is built, create a POD shuttle for it (if resources permit)
    # 4) Also create pods for any existing tubes that don't have a pod yet (simple pass)

    # Helper to increment occupancy estimate when we target a module
    def choose_target_module_for_landing(landing_bid, astro_type=None):
        # astro_type not used here (landings contain many astronauts of many types)
        # We'll pick module of the first astronaut type available (if present)
        info = buildings[landing_bid]
        if not info['landing']:
            # fallback: any module (choose nearest overall)
            candidates = [bid for bid, b in buildings.items() if b['type']=='module']
            if not candidates:
                return None
            candidates.sort(key=lambda m: dist(buildings[landing_bid], buildings[m]))
            return candidates[0]
        t = info['landing'][0]
        if t not in module_ids_by_type:
            # fallback to nearest module overall
            candidates = [bid for bid, b in buildings.items() if b['type']=='module']
            if not candidates:
                return None
            candidates.sort(key=lambda m: dist(buildings[landing_bid], buildings[m]))
            return candidates[0]
        candidates = module_ids_by_type[t][:]
        # sort by expected occupancy, then by distance
        candidates.sort(key=lambda m: (expected_occupancy.get(m,0), dist(buildings[landing_bid], buildings[m])))
        return candidates[0] if candidates else None

    # Build a tube (update state and resources)
    def build_tube(a, b, resources, actions):
        c = cost_tube(a,b)
        if c <= 0:
            c = 1
        if resources < c:
            return False, resources
        # double-check can build
        if not can_build_tube(a,b):
            return False, resources
        actions.append(f"TUBE {a} {b}")
        tubes.append((a,b,1))
        resources -= c
        return True, resources

    # Build teleport
    def build_teleport(a,b,resources,actions):
        if resources < 5000:
            return False, resources
        if have_teleport_endpoint(a) or have_teleport_endpoint(b):
            return False, resources
        teleports.add(frozenset({a,b}))
        actions.append(f"TELEPORT {a} {b}")
        resources -= 5000
        return True, resources

    # try to create shuttle pods on tubes that don't have a pod yet (simple)
    existing_tube_pairs = set(frozenset({a,b}) for (a,b,_) in tubes)
    pods_cover_pairs = set()
    for pid, route in pods.items():
        if len(route) >= 2:
            for i in range(len(route)-1):
                pods_cover_pairs.add(frozenset({route[i], route[i+1]}))

    # Create pods for tubes that lack one (greedy)
    for (a,b,_) in tubes:
        pair = frozenset({a,b})
        if pair not in pods_cover_pairs:
            # make a looping pod a-b-a to shuttle both ways
            if resources >= 1000:
                resources = try_create_pod([a,b,a], resources, actions)
                pods_cover_pairs.add(pair)

    # For each new landing, try to connect and create pods
    for bid in new_buildings_list:
        if buildings[bid]['type'] != 'landing':
            continue
        target = choose_target_module_for_landing(bid)
        if target is None:
            continue

        # Increment expected occupancy estimate for chosen target by number of arriving astronauts
        num_arrivals = len(buildings[bid]['landing'])
        expected_occupancy[target] = expected_occupancy.get(target, 0) + num_arrivals

        # Try direct tube
        if can_build_tube(bid, target):
            ok, resources = build_tube(bid, target, resources, actions)
            if ok:
                # create pod shuttle if possible
                resources = try_create_pod([bid, target, bid], resources, actions)
                continue
        # If direct tube impossible, try teleporter
        if not have_teleport_endpoint(bid) and not have_teleport_endpoint(target) and resources >= 5000:
            ok, resources = build_teleport(bid, target, resources, actions)
            if ok:
                # create a pod on arrival side if resources permit (not necessary)
                continue

        # Otherwise try to connect to a nearby building to make a chain:
        # find nearest building that we can connect to by tube and that lowers distance-to-target (by euclidean heuristic)
        best_candidate = None
        best_metric = float('inf')
        for other_id, other in buildings.items():
            if other_id == bid or other_id == target:
                continue
            if buildings[other_id]['type'] not in ('module','landing'):
                continue
            if not can_build_tube(bid, other_id):
                continue
            # heuristic metric: distance from other to target + small cost
            m = dist(buildings[other_id], buildings[target]) + 0.001 * dist(buildings[bid], buildings[other_id])
            if m < best_metric:
                best_metric = m
                best_candidate = other_id
        if best_candidate:
            ok, resources = build_tube(bid, best_candidate, resources, actions)
            if ok:
                resources = try_create_pod([bid, best_candidate, bid], resources, actions)
                # try to connect that candidate to target next turns or now if possible
                # attempt immediate connection candidate->target if possible and resources permit
                if can_build_tube(best_candidate, target) and resources >= cost_tube(best_candidate, target):
                    ok2, resources = build_tube(best_candidate, target, resources, actions)
                    if ok2:
                        resources = try_create_pod([best_candidate, target, best_candidate], resources, actions)
                continue

        # failing all above, wait (maybe we have not enough resources)
        # optionally create a cheap pod to move people to nearby building if any capsule route exists
        # (skipped to keep actions simple)

    # If no actions chosen, WAIT
    action_str = ";".join(actions) if actions else "WAIT"
    print(action_str, flush=True)

    first_turn = False
