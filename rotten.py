import sys
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


import pykraken as pk
import random
import time

TILE_SIZE = 32
GRID_WIDTH = 20
GRID_HEIGHT = 15

UI_LEFT = 100
UI_BOTTOM = 100

GRID_OFFSET_X = UI_LEFT
GRID_OFFSET_Y = 0

WIDTH = GRID_WIDTH * TILE_SIZE + UI_LEFT
HEIGHT = GRID_HEIGHT * TILE_SIZE + UI_BOTTOM

EMPTY, PLANT, ROT, BLOCKED = 0, 1, 2, 3

TOOL_WATER = 0
TOOL_CLEAN = 1
TOOL_BURN = 2
current_tool = TOOL_WATER

tool_cooldowns = [0, 0, 0]
tool_max_cooldowns = [1.0, 2.0, 5.0]

last_time = time.time()
tick_timer = 0
TICK_RATE = 0.5

score = 0
score_timer = 0
game_over = False

player_x = GRID_WIDTH // 2
player_y = GRID_HEIGHT // 2

rot_spread_chance = 0.05

plant_img = None
texture_loaded = False


###-- helper
def get_plant_stage(age):
    if age < 5:
        return 0  # fresh
    elif age < 10:
        return 1  # healthy
    else:
        return 2  # dying


def reset_game():
    global grid, score, player_x, player_y, game_over
    global tool_cooldowns, rot_spread_chance, message

    grid = [[{"type": EMPTY, "age": 0} for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    grid[GRID_HEIGHT // 2][GRID_WIDTH // 2] = {"type": ROT, "age": 0}

    score = 0
    player_x = GRID_WIDTH // 2
    player_y = GRID_HEIGHT // 2

    tool_cooldowns = [0, 0, 0]
    rot_spread_chance = 0.05

    message = "New run started!"
    game_over = False

pk.init()
pk.window.create("Life & Decay Garden ", pk.Vec2(WIDTH, HEIGHT))

grid = [[{"type": EMPTY, "age": 0} for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
grid[GRID_HEIGHT // 2][GRID_WIDTH // 2] = {"type": ROT, "age": 0}

font = pk.Font(resource_path("font.ttf"), 20)
message = "Welcome to Life & Decay! "


def update_world():
    global grid, rot_spread_chance

    rot_spread_chance += 0.001
    rot_count = 0

    new_grid = [[cell.copy() for cell in row] for row in grid]

    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            cell = grid[y][x]

            if cell["type"] == PLANT:
                new_grid[y][x]["age"] += 1
                if new_grid[y][x]["age"] > 15:
                    new_grid[y][x] = {"type": ROT, "age": 0}

            elif cell["type"] == ROT:
                new_grid[y][x]["age"] += 1
                rot_count += 1
                if rot_count > 20:
                    global game_over
                    game_over = True

                if random.random() < rot_spread_chance:
                    dx, dy = random.choice([(-1,0),(1,0),(0,-1),(0,1)])
                    nx, ny = x + dx, y + dy

                    if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                        neighbor = grid[ny][nx]

                        if neighbor["type"] == EMPTY:
                            new_grid[ny][nx] = {"type": ROT, "age": 0}

                        elif neighbor["type"] == PLANT:
                            if random.random() < rot_spread_chance * 0.5:
                                new_grid[ny][nx] = {"type": ROT, "age": 0}

    if random.random() < 0.05:
        rx = random.randint(0, GRID_WIDTH - 1)
        ry = random.randint(0, GRID_HEIGHT - 1)

        if grid[ry][rx]["type"] == EMPTY:
            new_grid[ry][rx] = {"type": PLANT, "age": 0}

    grid = new_grid


running = True

while running:

    # ---------------- INPUT ----------------
    for event in pk.event.poll():

        if event.type == pk.QUIT:
            running = False

        if event.type == pk.KEY_DOWN:
            if event.key == pk.K_r and game_over:
                reset_game()
            if event.key == pk.K_w:
                player_y = max(0, player_y - 1)
            elif event.key == pk.K_s:
                player_y = min(GRID_HEIGHT - 1, player_y + 1)
            elif event.key == pk.K_a:
                player_x = max(0, player_x - 1)
            elif event.key == pk.K_d:
                player_x = min(GRID_WIDTH - 1, player_x + 1)
            if event.key == pk.K_1:
                current_tool = TOOL_WATER
            elif event.key == pk.K_2:
                current_tool = TOOL_CLEAN
            elif event.key == pk.K_3:
                current_tool = TOOL_BURN    

        if event.type == pk.MOUSE_BUTTON_DOWN:
            mx, my = pk.mouse.get_pos()

            gx = int((mx - GRID_OFFSET_X) // TILE_SIZE)
            gy = int((my - GRID_OFFSET_Y) // TILE_SIZE)

            if 0 <= gx < GRID_WIDTH and 0 <= gy < GRID_HEIGHT:

                if abs(gx - player_x) <= 1 and abs(gy - player_y) <= 1:

                    cell = grid[gy][gx]

                    if current_tool == TOOL_WATER:
                        if cell["type"] == PLANT:
                            if tool_cooldowns[TOOL_WATER] <= 0:
                                cell["age"] = 0
                                tool_cooldowns[TOOL_WATER] = tool_max_cooldowns[TOOL_WATER]
                                score += 10
                                message = "Watered plant (+1). "

                    elif current_tool == TOOL_CLEAN:
                        if cell["type"] == ROT:
                            if tool_cooldowns[TOOL_CLEAN] <= 0:
                                grid[gy][gx] = {"type": EMPTY, "age": 0}
                                tool_cooldowns[TOOL_CLEAN] = tool_max_cooldowns[TOOL_CLEAN]
                                score += 10
                                message = "Cleaned rot (+1). "

                    elif current_tool == TOOL_BURN:
                        if tool_cooldowns[TOOL_BURN] <= 0:
                            grid[gy][gx] = {"type": BLOCKED, "age": 0}
                            tool_cooldowns[TOOL_BURN] = tool_max_cooldowns[TOOL_BURN]
                            score -= 10
                            message = "Burned tile (-1). "

            for i in range(3):
                bx, by = 10, 10 + i * 60
                if bx <= mx <= bx + 80 and by <= my <= by + 50:
                    current_tool = i

    # ---------------- UPDATE ----------------
    dt = time.time() - last_time
    last_time = time.time()

    tick_timer += dt

    score_timer += dt

    if score_timer >= 1.0:
        score_timer -= 1.0
        score += 1

    if tick_timer >= TICK_RATE:
        tick_timer -= TICK_RATE
        update_world()

    for i in range(3):
        tool_cooldowns[i] = max(0, tool_cooldowns[i] - dt)
    # ---------------- DRAW ----------------
    if not texture_loaded:
        plant_img = pk.Texture(resource_path("PlantA.png"))
        texture_loaded = True

    if game_over:        
        # Draw a semi-transparent overlay for better text visibility
        pk.renderer.clear((0, 0, 0))
        
        # Center the game over text
        font.draw("GAME OVER", pk.Vec2(WIDTH//2 - 80, HEIGHT//2 - 50), pk.Color(255, 50, 50))
        font.draw("Final Score: " + str(score), pk.Vec2(WIDTH//2 - 80, HEIGHT//2), pk.Color(255, 255, 255))
        font.draw("Press R to Restart", pk.Vec2(WIDTH//2 - 100, HEIGHT//2 + 50), pk.Color(200, 200, 200))
        
        pk.renderer.present()
        continue
    # ---------------- DRAW ui outlines ----------------
    pk.renderer.clear((30, 30, 30))

    pk.draw.rect(pk.Rect(0, 0, UI_LEFT, HEIGHT), pk.Color(50, 50, 50))
    pk.draw.rect(pk.Rect(0, HEIGHT - UI_BOTTOM, WIDTH, UI_BOTTOM), pk.Color(40, 40, 40))

    # -------- GRID (FIXED ORDER) --------
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):

            tile = grid[y][x]

            x_pos = GRID_OFFSET_X + x * TILE_SIZE
            y_pos = GRID_OFFSET_Y + y * TILE_SIZE

            in_range = abs(x - player_x) <= 1 and abs(y - player_y) <= 1

            # ---------------- EMPTY ----------------
            if tile["type"] == EMPTY:
                pk.draw.rect(
                    pk.Rect(x_pos, y_pos, TILE_SIZE - 1, TILE_SIZE - 1),
                    pk.Color(120, 80, 40)
                )

            # ---------------- PLANT (STAGES) ----------------
            elif tile["type"] == PLANT:
                stage = get_plant_stage(tile["age"])

                pk.renderer.draw(
                    plant_img,
                    pk.Rect(x_pos, y_pos, TILE_SIZE, TILE_SIZE)
                )

                # dying warning overlay
                if stage == 2:
                    pk.draw.rect(
                        pk.Rect(x_pos, y_pos, TILE_SIZE, TILE_SIZE),
                        pk.Color(255, 80, 80, 60)
                    )

            # ---------------- ROT (STAINED + ORGANIC) ----------------
            elif tile["type"] == ROT:
                age = tile["age"]

                base_color = pk.Color(
                    120,
                    max(10, 60 - age * 2),
                    20
                )

                pk.draw.rect(
                    pk.Rect(x_pos, y_pos, TILE_SIZE - 1, TILE_SIZE - 1),
                    base_color
                )

                # infection stain overlay (key visual improvement)
                stain_alpha = min(140, age * 6)

                pk.draw.rect(
                    pk.Rect(x_pos, y_pos, TILE_SIZE, TILE_SIZE),
                    pk.Color(90, 0, 0, stain_alpha)
                )

            # ---------------- BLOCKED ----------------
            elif tile["type"] == BLOCKED:
                pk.draw.rect(
                    pk.Rect(x_pos, y_pos, TILE_SIZE - 1, TILE_SIZE - 1),
                    pk.Color(0, 0, 0)
                )

            # ---------------- RANGE HIGHLIGHT ----------------
            if in_range:
                pk.draw.rect(
                    pk.Rect(x_pos, y_pos, TILE_SIZE - 1, TILE_SIZE - 1),
                    pk.Color(255, 255, 255),
                    2
                )
    # -------- UI BUTTONS --------
    tool_names = ["Water[1]! ", "Clean[2]! ", "Burn[3]! "]

    for i in range(3):
        bx, by = 10, 10 + i * 60

        cooldown = tool_cooldowns[i]
        max_cd = tool_max_cooldowns[i]

        color = pk.Color(140, 140, 140) if i == current_tool else pk.Color(80, 80, 80)

        pk.draw.rect(pk.Rect(bx, by, 80, 50), color)

        if cooldown > 0:
            ratio = cooldown / max_cd
            pk.draw.rect(
                pk.Rect(bx, by, 80, int(50 * ratio)),
                pk.Color(0, 0, 0, 120)
            )

        font.draw(tool_names[i], pk.Vec2(bx + 5, by + 15), pk.Color(255, 255, 255))

    # -------- PLAYER --------
    pk.draw.rect(
        pk.Rect(
            GRID_OFFSET_X + player_x * TILE_SIZE,
            GRID_OFFSET_Y + player_y * TILE_SIZE,
            TILE_SIZE - 1,
            TILE_SIZE - 1
        ),
        pk.Color(50, 150, 255)
    )

    font.draw(message, pk.Vec2(10, HEIGHT - UI_BOTTOM + 10), pk.Color(255, 255, 255))

    score_text = "Score: " + str(score)
    font.draw(score_text, pk.Vec2(10, HEIGHT - UI_BOTTOM - 100), pk.Color(255, 255, 255))

    pk.renderer.present()

pk.quit()
