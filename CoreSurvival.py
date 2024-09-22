import math
import pygame
import pygame_gui
import random

pygame.init()

#region --- variables ---
#region --main loop variables--
start_ticks = pygame.time.get_ticks()
running = True
display_info = pygame.display.Info()
screen = pygame.display.set_mode(pygame.Vector2(display_info.current_w, display_info.current_h), pygame.FULLSCREEN)
clock = pygame.time.Clock()
#endregion

#region --player stats--
player_points = 0
player_coins = 0
player_wood = 0
player_stone = 0
#endregion

#region --list initialization--
items_list = []
bullet_list = []
enemy_list = []
#endregion

#region --positional initialization--
center = pygame.Vector2(display_info.current_w / 2, display_info.current_h / 2)
random_range_x = display_info.current_w
random_range_y = display_info.current_h
#endregion

#region --UI initialization--
UI_Manager = pygame_gui.UIManager((display_info.current_w, display_info.current_h))
UI_items = pygame_gui.elements.UITextBox('', pygame.Rect(0, 0, 100, 100), UI_Manager)
UI_mouse_pos = pygame_gui.elements.UITextBox('', pygame.Rect(0, 0, 0, 0), UI_Manager)
UI_info = pygame_gui.elements.UITextBox('esc: close game\n'
                                        'wasd: walking\n'
                                        'mouse: aiming\n'
                                        'Spacebar: shooting\n', pygame.Rect(display_info.current_w - 300, 0, 300, 150), UI_Manager)
#endregion

#region --EVENT--
TIMER_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(TIMER_EVENT, 500)
frame = 0
#endregion

#region --image initialization--

def scale_image(img, image_scale):
    scaled = pygame.Vector2(img.get_width() * image_scale, img.get_height() * image_scale)
    scaled_img = pygame.transform.scale(img, scaled)
    return scaled_img

IMAGE_OFFSET = -90
idle_player_image = pygame.image.load('Sprites/Player/player_stat.png').convert_alpha()
shooting_player_image = pygame.image.load('Sprites/Player/player_aim.png').convert_alpha()

enemy_img = pygame.image.load('Sprites/Enemy/enemy_stat.png').convert_alpha()
bullet_img = scale_image(pygame.image.load('Sprites/Items/bullet.png').convert_alpha(), 0.3)
coin_img = pygame.image.load('Sprites/Items/coin.png').convert_alpha()
#endregion
#endregion

#region --- Classes and functions ---
def random_pos():
    return pygame.Vector2(random.randint(0, display_info.current_w), random.randint(0, display_info.current_h))

def get_mouse_pos():
    pos = pygame.mouse.get_pos()
    return pos

def get_direction(target, current):
    return pygame.Vector2(target) - current

def rotate_img(target_pos, current_pos, offset):
    # get angle by taking direction converting that in radians and then the radian to degrees
    # offset want sprites zijn richting boven gemaakt terwijl default rechts is

    direction = get_direction(target_pos, current_pos)
    # calculate direction by subtracting current pos from mouse pos
    # mouse_pos [1500, 700] - current_pos [700, 450] = direction [800, 250]

    angle = math.degrees(math.atan2(direction.y, direction.x))
    # [direction.y / direction.x] [250 / 800] = arc tangent is 0.3125
    # 0.3125 * (180 / pi) = angle is 17,9 graden

    return -angle + offset

class Player:
    def __init__(self):
        self.speed = 3

        self.original_idle_img = idle_player_image
        self.idle_img = self.original_idle_img

        self.original_shooting_img = shooting_player_image
        self.shooting_img = self.original_shooting_img

        self.current_state = 'idle'
        self.current_image = self.idle_img
        self.current_original_image = self.original_idle_img

        #pos
        self.move = pygame.Vector2(0, 0)
        self.pos = pygame.Vector2(center.x, center.y)
        self.rect = pygame.Rect(self.pos.x, self.pos.y, self.current_original_image.get_width(), self.current_original_image.get_height())

    def move_pos(self):
        self.pos.x += self.move.x * self.speed
        self.pos.y += self.move.y * self.speed
        self.rect.center = (self.pos.x, self.pos.y)

    def handle_input(self):
        global running
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            print(f'user input, Exit game')
            running = False
        if pygame.key.get_just_pressed()[pygame.K_SPACE]:
            bullet_list.append(Bullet())
        self.move.x = (keys[pygame.K_d] - keys[pygame.K_a])
        self.move.y = (keys[pygame.K_s] - keys[pygame.K_w])

    def collision(self):
        global player_points
        global player_coins
        for item in items_list:
            collided = self.rect.colliderect(item)
            if collided:
                items_list.remove(item)
                player_points += 9
                player_coins += 10

    def draw(self):
        pygame.draw.rect(screen, 'red', self.rect, 5)
        screen.blit(self.current_image, (
        self.rect.centerx - self.current_image.get_width() / 2, self.rect.centery - self.current_image.get_height() / 2))

    def manager(self):
        self.handle_input()

        if self.move:
            self.current_state = 'shooting'
            self.current_original_image = self.original_shooting_img
            self.current_image = self.shooting_img
        else:
            self.current_state = 'idle'
            self.current_original_image = self.original_idle_img
            self.current_image = self.idle_img

        self.move_pos()
        self.current_image = pygame.transform.rotate(self.current_image, rotate_img(get_mouse_pos(), self.rect.center, IMAGE_OFFSET))
        self.draw()
        self.collision()

class Bullet:
    def __init__(self):
        self.is_alive = True
        self.speed = 25

        self.original_image = bullet_img
        self.image = self.original_image

        self.rect = self.original_image.get_rect()
        self.pos = pygame.Vector2(player.pos)

        self.direction = get_direction(get_mouse_pos(), player.rect.center)
        self.normalized_direction = self.direction
        #region normalize direction
        try:
            self.normalized_direction.normalize_ip()
        except ValueError:
            print(f'Cannot normalize vector 0')
        #endregion

        self.target = get_mouse_pos()
        self.angle = math.degrees(math.atan2(self.direction.y, self.direction.x))
        self.angle = -self.angle + IMAGE_OFFSET

    def move_self(self):
        self.pos += self.direction * self.speed
        self.rect.center = self.pos

    def collision(self):
        global player_points
        global player_coins
        for enemy in enemy_list:
            collided = self.rect.colliderect(enemy)
            if collided:
                enemy_list.remove(enemy)
                #Get points per hit, buying items or doing something
                player_points += 18
                #Get coins after killing a enemy
                player_coins += 5
                self.is_alive = False
            if (self.rect.x <= 0 or self.rect.x >= display_info.current_w or
                    self.rect.y <= 0 or self.rect.y > display_info.current_h):
                self.is_alive = False

    def draw(self):
        pygame.draw.rect(screen, 'red', self.rect, 2) #border
        screen.blit(self.image, self.rect)

    def manager(self):
        self.move_self()
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.draw()
        self.collision()

class Enemy:
    def __init__(self):
        self.max_dist = 250
        self.min_dist = 50
        self.original_image = enemy_img
        self.image = self.original_image

        self.current_pos = random_pos()
        self.rect = pygame.Rect(self.current_pos.x, self.current_pos.y, self.image.width, self.image.height)

        #enemy base stats
        self.enemy_health = 100

    def rot_enemy(self, target_pos):
        direction = pygame.Vector2(target_pos) - pygame.Vector2(self.rect.center)
        angle = math.degrees(math.atan2(direction.y, direction.x))

        #convert img rot to face towards player with offset since wrong front plane
        offset = -90
        self.image = pygame.transform.rotate(self.original_image, -angle + offset)
        self.rect = self.image.get_rect(center=self.rect.center)

    def move_towards(self, target_pos):
        current_pos = pygame.math.Vector2(self.rect.x, self.rect.y)
        distance = current_pos.distance_to(target_pos)
        direction = target_pos - current_pos

        try:
            direction.normalize_ip()
        except ValueError:
            return "Cant normalize vector of zero"

        if distance <= self.max_dist:
            if distance <= self.min_dist:
                return
            else:
                self.rot_enemy(target_pos)
                self.rect.topleft += direction * 5

    def draw(self):
        pygame.draw.rect(screen, 'red', self.rect, 5) #border
        screen.blit(self.image, self.rect)

    def manager(self, target_pos):
        self.draw()
        self.move_towards(target_pos)

#region -- item classes --
class Item:
    def __init__(self):
        self.pos = random_pos()
        self.coin_img = coin_img
        self.rect = pygame.Rect(self.pos.x, self.pos.y, self.coin_img.get_width(), self.coin_img.get_height())

class Coins(Item):
    def draw(self):
        pygame.draw.rect(screen, 'red', self.rect, 5)
        screen.blit(self.coin_img, self.pos)

class Wood(Item):
    def draw(self):
        pygame.draw.rect(screen, 'red', self.rect, 5)
        screen.blit(self.coin_img, self.pos)

class Stone(Item):
    def draw(self):
        pygame.draw.rect(screen, 'red', self.rect, 5)
        screen.blit(self.coin_img, self.pos)

for _ in range(10):
    items_list.append(Stone())
    items_list.append(Wood())
    items_list.append(Coins())

def draw_items():
    for item in items_list:
        item.draw()
#endregion
#endregion

#region --- initialization ---
#region -- initializing enemies --
enemy_amount = 10
enemy_list = [Enemy() for enemies in range(enemy_amount)]
#endregion

#region -- initializing player --
player = Player()
#endregion
#endregion

#region --- Main loop ---
while running:
    #region event loop
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == TIMER_EVENT:
            if frame == 3:
                frame = 0
            else: frame += 1
    screen.fill('green')
    #endregion

    #region --object update--
    player.manager()

    for bullet in bullet_list:
        if bullet.is_alive:
            Bullet.manager(bullet)
        else:
            bullet_list.remove(bullet)

    draw_items()

    for enemies in enemy_list:
        Enemy.manager(enemies, player.pos)
    #endregion

    #region --UI update--
    mousex, mousey = get_mouse_pos()
    UI_mouse_pos.rect = pygame.Rect(mousex, mousey, 200, 100)
    seconds = (pygame.time.get_ticks()-start_ticks)/1000
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    formatted_time = f"{minutes:02}:{seconds:02}"
    UI_items.set_text(f'Time: {formatted_time} \npoints: {player_points}\ncoins: {player_coins}')
    UI_mouse_pos.set_text(f'playerpos: {player.rect.centerx},{player.rect.centery}\nmousepos: {mousex}, {mousey}\ndistance: {get_direction(get_mouse_pos(), player.rect.center)}\n')
    UI_Manager.update(clock.tick(60)/1000.0)
    UI_Manager.draw_ui(screen)
    #endregion

    #region Refresh screen and set fps
    pygame.display.flip()
    clock.tick(60)
    #endregion
#endregion

#Quit if main loop breaks
pygame.quit()