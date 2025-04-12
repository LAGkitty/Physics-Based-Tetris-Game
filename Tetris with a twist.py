import pygame
import pymunk
import sys
import random
import math
from pymunk import Vec2d

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
GRID_OFFSET_X = (WIDTH - GRID_WIDTH * BLOCK_SIZE) // 2
GRID_OFFSET_Y = 40
BORDER_WIDTH = 4
GRAVITY = 500
SHAKE_FORCE = 2000
SHAKE_DURATION = 100  # milliseconds

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (40, 40, 40)
DARK_GRAY = (20, 20, 20)
GRID_COLOR = (50, 50, 50)
BORDER_COLOR = (100, 100, 100)

# Tetromino colors
COLORS = [
    (0, 0, 0),        # Empty
    (0, 240, 240),    # I - Cyan
    (0, 0, 240),      # J - Blue
    (240, 160, 0),    # L - Orange
    (240, 240, 0),    # O - Yellow
    (0, 240, 0),      # S - Green
    (160, 0, 240),    # T - Purple
    (240, 0, 0)       # Z - Red
]

# Tetromino shapes (x, y) coordinates
SHAPES = [
    [],  # Empty
    [(0, 0), (0, -1), (0, 1), (0, 2)],      # I
    [(0, 0), (0, -1), (0, 1), (-1, 1)],     # J
    [(0, 0), (0, -1), (0, 1), (1, 1)],      # L
    [(0, 0), (1, 0), (0, 1), (1, 1)],       # O
    [(0, 0), (1, 0), (0, -1), (-1, -1)],    # S
    [(0, 0), (-1, 0), (1, 0), (0, 1)],      # T
    [(0, 0), (-1, 0), (0, -1), (1, -1)]     # Z
]

# Create the window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Physics Tetris")
clock = pygame.time.Clock()

# Create physics space
space = pymunk.Space()
space.gravity = (0, GRAVITY)

# Create game borders
def create_segment(p1, p2, thickness=BORDER_WIDTH):
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    shape = pymunk.Segment(body, p1, p2, thickness)
    shape.elasticity = 0.5
    shape.friction = 0.9
    shape.collision_type = 1
    space.add(body, shape)
    return shape

# Create the border of the game area
left_wall = create_segment(
    (GRID_OFFSET_X - BORDER_WIDTH, GRID_OFFSET_Y - BORDER_WIDTH),
    (GRID_OFFSET_X - BORDER_WIDTH, GRID_OFFSET_Y + GRID_HEIGHT * BLOCK_SIZE + BORDER_WIDTH)
)
right_wall = create_segment(
    (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + BORDER_WIDTH, GRID_OFFSET_Y - BORDER_WIDTH),
    (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + BORDER_WIDTH, GRID_OFFSET_Y + GRID_HEIGHT * BLOCK_SIZE + BORDER_WIDTH)
)
bottom_wall = create_segment(
    (GRID_OFFSET_X - BORDER_WIDTH, GRID_OFFSET_Y + GRID_HEIGHT * BLOCK_SIZE + BORDER_WIDTH),
    (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + BORDER_WIDTH, GRID_OFFSET_Y + GRID_HEIGHT * BLOCK_SIZE + BORDER_WIDTH)
)

class Block:
    def __init__(self, space, pos, color, block_type, mass=1.0):
        # Convert grid position to screen coordinates
        x = GRID_OFFSET_X + pos[0] * BLOCK_SIZE + BLOCK_SIZE // 2
        y = GRID_OFFSET_Y + pos[1] * BLOCK_SIZE + BLOCK_SIZE // 2
        
        # Create physics body
        self.body = pymunk.Body(mass=mass, moment=pymunk.moment_for_box(mass, (BLOCK_SIZE - 2, BLOCK_SIZE - 2)))
        self.body.position = x, y
        
        # Create shape
        self.shape = pymunk.Poly.create_box(self.body, (BLOCK_SIZE - 2, BLOCK_SIZE - 2))
        self.shape.elasticity = 0.1
        self.shape.friction = 0.8
        self.shape.collision_type = 2
        
        # Add to space
        space.add(self.body, self.shape)
        
        self.color = color
        self.block_type = block_type
        self.grid_pos = None  # Will be updated during game updates
    
    def draw(self, surface):
        pos = self.body.position
        vertices = [self.body.local_to_world(v) for v in self.shape.get_vertices()]
        
        # Draw the block
        pygame.draw.polygon(surface, self.color, vertices)
        pygame.draw.polygon(surface, tuple(max(0, c - 50) for c in self.color), vertices, 2)
    
    def update_grid_position(self):
        x = int((self.body.position.x - GRID_OFFSET_X) / BLOCK_SIZE)
        y = int((self.body.position.y - GRID_OFFSET_Y) / BLOCK_SIZE)
        
        # Ensure position is within grid bounds
        x = max(0, min(x, GRID_WIDTH - 1))
        y = max(0, min(y, GRID_HEIGHT - 1))
        
        self.grid_pos = (x, y)
        return self.grid_pos

class Tetromino:
    def __init__(self, tetromino_type=None):
        # Select a random tetromino if none specified
        if tetromino_type is None:
            tetromino_type = random.randint(1, 7)
        
        self.type = tetromino_type
        self.color = COLORS[tetromino_type]
        self.blocks = []
        self.shape_coords = SHAPES[tetromino_type]
        
        # Initial position (centered at top)
        self.grid_x = GRID_WIDTH // 2
        self.grid_y = 1
        
        # Physics blocks will be created when the tetromino is locked

    def create_physics_blocks(self, space):
        blocks = []
        for coord in self.shape_coords:
            x = self.grid_x + coord[0]
            y = self.grid_y + coord[1]
            block = Block(space, (x, y), self.color, self.type)
            blocks.append(block)
        return blocks

    def draw_preview(self, surface):
        for coord in self.shape_coords:
            x = self.grid_x + coord[0]
            y = self.grid_y + coord[1]
            
            # Only draw if within the grid area
            if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                screen_x = GRID_OFFSET_X + x * BLOCK_SIZE
                screen_y = GRID_OFFSET_Y + y * BLOCK_SIZE
                
                pygame.draw.rect(surface, self.color, 
                                (screen_x + 1, screen_y + 1, BLOCK_SIZE - 2, BLOCK_SIZE - 2))
                pygame.draw.rect(surface, tuple(max(0, c - 50) for c in self.color), 
                                (screen_x + 1, screen_y + 1, BLOCK_SIZE - 2, BLOCK_SIZE - 2), 2)
    
    def move(self, dx, dy, grid):
        # Check if movement is valid
        for coord in self.shape_coords:
            new_x = self.grid_x + dx + coord[0]
            new_y = self.grid_y + dy + coord[1]
            
            # Check boundaries
            if (new_x < 0 or new_x >= GRID_WIDTH or 
                new_y >= GRID_HEIGHT or 
                (new_y >= 0 and grid[new_y][new_x] != 0)):
                return False
        
        # Move if valid
        self.grid_x += dx
        self.grid_y += dy
        return True

    def rotate(self, grid):
        # Create a copy of current shape
        old_coords = self.shape_coords.copy()
        
        # Rotate 90 degrees clockwise
        new_coords = [(coord[1], -coord[0]) for coord in old_coords]
        self.shape_coords = new_coords
        
        # Check if rotation is valid
        for coord in self.shape_coords:
            x = self.grid_x + coord[0]
            y = self.grid_y + coord[1]
            
            # Check boundaries
            if (x < 0 or x >= GRID_WIDTH or 
                y >= GRID_HEIGHT or 
                (y >= 0 and grid[y][x] != 0)):
                # Restore old shape if invalid
                self.shape_coords = old_coords
                return False
        
        return True

class Game:
    def __init__(self):
        # Clear any existing physics objects
        global space
        for body in space.bodies[:]:
            space.remove(body)
        for shape in space.shapes[:]:
            if shape.body and shape.body in space.bodies:
                continue  # Shape will be removed when its body is removed
            space.remove(shape)
        
        # Recreate the borders
        global left_wall, right_wall, bottom_wall
        left_wall = create_segment(
            (GRID_OFFSET_X - BORDER_WIDTH, GRID_OFFSET_Y - BORDER_WIDTH),
            (GRID_OFFSET_X - BORDER_WIDTH, GRID_OFFSET_Y + GRID_HEIGHT * BLOCK_SIZE + BORDER_WIDTH)
        )
        right_wall = create_segment(
            (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + BORDER_WIDTH, GRID_OFFSET_Y - BORDER_WIDTH),
            (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + BORDER_WIDTH, GRID_OFFSET_Y + GRID_HEIGHT * BLOCK_SIZE + BORDER_WIDTH)
        )
        bottom_wall = create_segment(
            (GRID_OFFSET_X - BORDER_WIDTH, GRID_OFFSET_Y + GRID_HEIGHT * BLOCK_SIZE + BORDER_WIDTH),
            (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + BORDER_WIDTH, GRID_OFFSET_Y + GRID_HEIGHT * BLOCK_SIZE + BORDER_WIDTH)
        )
        
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.blocks = []
        self.current_tetromino = Tetromino()
        self.next_tetromino = Tetromino()
        self.game_over = False
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.fall_time = 0
        self.fall_speed = 500  # milliseconds
        self.lock_delay = 500  # milliseconds
        self.lock_time = 0
        self.is_locking = False
        self.shake_time = 0
        self.mouse_active = False
        self.mouse_pos = (0, 0)
        
        # Grid for debugging
        self.debug_grid = False
    
    def apply_shake(self, shake_x, shake_y):
        # Apply force to all blocks
        for block in self.blocks:
            force = Vec2d(shake_x * SHAKE_FORCE, shake_y * SHAKE_FORCE)
            block.body.apply_force_at_local_point(force, (0, 0))
        
        self.shake_time = SHAKE_DURATION
    
    def update_grid_from_blocks(self):
        # Clear grid
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        
        # Update grid based on block positions
        for block in self.blocks:
            x, y = block.update_grid_position()
            
            # Only update if block is inside grid boundaries
            if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                self.grid[y][x] = block.block_type
    
    def update(self, dt):
        if self.game_over:
            return
        
        # Update physics
        space.step(dt / 1000.0)
        
        # Update grid based on current block positions
        self.update_grid_from_blocks()
        
        # Update shake effect
        if self.shake_time > 0:
            self.shake_time -= dt
        
        # Handle mouse movement for window shaking
        if self.mouse_active:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            dx = (mouse_x - self.mouse_pos[0]) / 10.0
            dy = (mouse_y - self.mouse_pos[1]) / 10.0
            
            if abs(dx) > 0.5 or abs(dy) > 0.5:
                self.apply_shake(dx, dy)
            
            self.mouse_pos = (mouse_x, mouse_y)
        
        # Update tetromino fall
        self.fall_time += dt
        if self.fall_time >= self.fall_speed:
            self.fall_time = 0
            
            # Try to move tetromino down
            if not self.current_tetromino.move(0, 1, self.grid):
                if not self.is_locking:
                    self.is_locking = True
                    self.lock_time = 0
        
        # Update lock delay
        if self.is_locking:
            self.lock_time += dt
            if self.lock_time >= self.lock_delay:
                self.lock_tetromino()
                self.clear_lines()
                self.spawn_tetromino()
                self.is_locking = False
    
    def lock_tetromino(self):
        # Create physics blocks for the tetromino
        new_blocks = self.current_tetromino.create_physics_blocks(space)
        self.blocks.extend(new_blocks)
        
        # Update grid
        for coord in self.current_tetromino.shape_coords:
            x = self.current_tetromino.grid_x + coord[0]
            y = self.current_tetromino.grid_y + coord[1]
            
            if 0 <= y < GRID_HEIGHT and 0 <= x < GRID_WIDTH:
                self.grid[y][x] = self.current_tetromino.type
        
        # Increase score
        self.score += 10
    
    def clear_lines(self):
        # First check which rows are full
        full_rows = []
        for y in range(GRID_HEIGHT):
            if all(cell != 0 for cell in self.grid[y]):
                full_rows.append(y)
        
        if not full_rows:
            return  # No full rows
        
        lines_cleared = len(full_rows)
        
        # Remove blocks in full rows
        for row_y in full_rows:
            blocks_to_remove = []
            for block in self.blocks:
                x, y = block.update_grid_position()
                if y == row_y:
                    blocks_to_remove.append(block)
            
            for block in blocks_to_remove:
                if block in self.blocks:  # Check if block still exists
                    self.blocks.remove(block)
                    space.remove(block.body, block.shape)
        
        # Apply gravity on blocks above removed rows
        for block in self.blocks:
            x, y = block.update_grid_position()
            drop_count = sum(1 for row_y in full_rows if y < row_y)
            if drop_count > 0:
                block.body.position += (0, drop_count * BLOCK_SIZE)
        
        # Update score and level
        points = [0, 40, 100, 300, 1200][min(lines_cleared, 4)] * self.level
        self.score += points
        self.lines_cleared += lines_cleared
        
        # Level up every 10 lines
        self.level = self.lines_cleared // 10 + 1
        
        # Increase fall speed with level
        self.fall_speed = max(100, 500 - (self.level - 1) * 20)
        
        # Update grid after clearing
        self.update_grid_from_blocks()
    
    def spawn_tetromino(self):
        self.current_tetromino = self.next_tetromino
        self.next_tetromino = Tetromino()
        
        # Check if game over (collision on spawn)
        for coord in self.current_tetromino.shape_coords:
            x = self.current_tetromino.grid_x + coord[0]
            y = self.current_tetromino.grid_y + coord[1]
            
            if 0 <= y < GRID_HEIGHT and 0 <= x < GRID_WIDTH and self.grid[y][x] != 0:
                self.game_over = True
                break
    
    def draw(self, surface):
        # Draw background
        surface.fill(BLACK)
        
        # Draw grid
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                rect = (
                    GRID_OFFSET_X + x * BLOCK_SIZE,
                    GRID_OFFSET_Y + y * BLOCK_SIZE,
                    BLOCK_SIZE,
                    BLOCK_SIZE
                )
                # Draw occupied cells differently if debug grid is on
                if self.debug_grid and self.grid[y][x] != 0:
                    pygame.draw.rect(surface, (100, 0, 0), rect, 0)
                pygame.draw.rect(surface, GRID_COLOR, rect, 1)
        
        # Draw border
        pygame.draw.rect(surface, BORDER_COLOR, (
            GRID_OFFSET_X - BORDER_WIDTH,
            GRID_OFFSET_Y - BORDER_WIDTH,
            GRID_WIDTH * BLOCK_SIZE + BORDER_WIDTH * 2,
            GRID_HEIGHT * BLOCK_SIZE + BORDER_WIDTH * 2
        ), BORDER_WIDTH)
        
        # Draw physics blocks
        for block in self.blocks:
            block.draw(surface)
        
        # Draw current tetromino preview
        if not self.game_over:
            self.current_tetromino.draw_preview(surface)
        
        # Draw next tetromino
        self.draw_next_tetromino(surface)
        
        # Draw UI
        self.draw_ui(surface)
        
        # Draw game over
        if self.game_over:
            self.draw_game_over(surface)
    
    def draw_next_tetromino(self, surface):
        # Draw next tetromino box
        next_box_x = GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + 40
        next_box_y = GRID_OFFSET_Y + 20
        next_box_width = 150
        next_box_height = 100
        
        pygame.draw.rect(surface, DARK_GRAY, (
            next_box_x,
            next_box_y,
            next_box_width,
            next_box_height
        ))
        
        pygame.draw.rect(surface, BORDER_COLOR, (
            next_box_x,
            next_box_y,
            next_box_width,
            next_box_height
        ), 2)
        
        font = pygame.font.SysFont('Arial', 20)
        text = font.render("Next:", True, WHITE)
        surface.blit(text, (next_box_x + 10, next_box_y + 10))
        
        # Draw next tetromino
        for coord in self.next_tetromino.shape_coords:
            x = coord[0] + 2  # Center in the box
            y = coord[1] + 2
            screen_x = next_box_x + (x + 1) * BLOCK_SIZE
            screen_y = next_box_y + (y + 1) * BLOCK_SIZE
            
            pygame.draw.rect(surface, self.next_tetromino.color, 
                           (screen_x, screen_y, BLOCK_SIZE - 2, BLOCK_SIZE - 2))
            pygame.draw.rect(surface, tuple(max(0, c - 50) for c in self.next_tetromino.color), 
                           (screen_x, screen_y, BLOCK_SIZE - 2, BLOCK_SIZE - 2), 2)
    
    def draw_ui(self, surface):
        # Draw score and level
        font = pygame.font.SysFont('Arial', 24)
        
        # Score
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        surface.blit(score_text, (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + 40, GRID_OFFSET_Y + 140))
        
        # Level
        level_text = font.render(f"Level: {self.level}", True, WHITE)
        surface.blit(level_text, (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + 40, GRID_OFFSET_Y + 180))
        
        # Lines cleared
        lines_text = font.render(f"Lines: {self.lines_cleared}", True, WHITE)
        surface.blit(lines_text, (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + 40, GRID_OFFSET_Y + 220))
        
        # Controls
        controls_y = GRID_OFFSET_Y + 280
        small_font = pygame.font.SysFont('Arial', 16)
        
        controls = [
            "Controls:",
            "Arrow Keys - Move",
            "Up - Rotate",
            "Space - Hard Drop",
            "P - Pause",
            "R - Restart",
            "D - Toggle Debug Grid",
            "Shake mouse - Move blocks"
        ]
        
        for i, line in enumerate(controls):
            text = small_font.render(line, True, WHITE)
            surface.blit(text, (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + 40, controls_y + i * 20))
    
    def draw_game_over(self, surface):
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        
        # Game over text
        font = pygame.font.SysFont('Arial', 48)
        game_over_text = font.render("GAME OVER", True, WHITE)
        text_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
        surface.blit(game_over_text, text_rect)
        
        # Final score
        font = pygame.font.SysFont('Arial', 32)
        score_text = font.render(f"Final Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
        surface.blit(score_text, score_rect)
        
        # Restart prompt
        font = pygame.font.SysFont('Arial', 24)
        restart_text = font.render("Press R to restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70))
        surface.blit(restart_text, restart_rect)
    
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.game_over:
                if event.key == pygame.K_r:
                    self.__init__()
                return
            
            if event.key == pygame.K_LEFT:
                self.current_tetromino.move(-1, 0, self.grid)
            elif event.key == pygame.K_RIGHT:
                self.current_tetromino.move(1, 0, self.grid)
            elif event.key == pygame.K_DOWN:
                self.current_tetromino.move(0, 1, self.grid)
            elif event.key == pygame.K_UP:
                self.current_tetromino.rotate(self.grid)
            elif event.key == pygame.K_SPACE:
                # Hard drop
                while self.current_tetromino.move(0, 1, self.grid):
                    self.score += 2
                self.lock_tetromino()
                self.clear_lines()
                self.spawn_tetromino()
            elif event.key == pygame.K_p:
                # Pause (not implemented)
                pass
            elif event.key == pygame.K_r:
                # Restart
                self.__init__()
            elif event.key == pygame.K_d:
                # Toggle debug grid
                self.debug_grid = not self.debug_grid
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                self.mouse_active = True
                self.mouse_pos = pygame.mouse.get_pos()
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left mouse button
                self.mouse_active = False

# Main game loop
def main():
    game = Game()
    
    while True:
        dt = clock.tick(60)  # Limit to 60 FPS
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            game.handle_input(event)
        
        game.update(dt)
        game.draw(screen)
        
        pygame.display.flip()

if __name__ == "__main__":
    main()