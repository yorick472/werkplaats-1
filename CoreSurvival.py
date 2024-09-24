import math
import pygame
import pygame_gui
import random

pygame.init()

#region --- variables ---
#region --main loop variables--
RUNNING, PAUSED, EXIT, START = 0, 1, 2, 3
state = RUNNING
start_ticks = pygame.time.get_ticks()
display_info = pygame.display.Info()
screen = pygame.display.set_mode(pygame.Vector2(display_info.current_w, display_info.current_h), pygame.FULLSCREEN)
clock = pygame.time.Clock()
#endregion
game_start_scherm = True
game_main = False
#region --player stats--
player_kill_count = 0
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
coin_img = scale_image(pygame.image.load('Sprites/Items/coin.png').convert_alpha(), 0.3)
#endregion
#endregion

#region --- Classes and functions ---
def get_time():
    time = (pygame.time.get_ticks() - start_ticks) / 1000
    return time

def convert_time():
    time = get_time()
    minutes = int(time // 60)
    seconds = int(time % 60)
    formatted_time = f"{minutes:02}:{seconds:02}"
    return formatted_time

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

def outer_spawn_pos():
        left_spawn_area = pygame.Vector2(0 - enemy_img.width, random.randint(0, display_info.current_h))
        right_spawn_area = pygame.Vector2(display_info.current_w + enemy_img.width, random.randint(0, display_info.current_h))
        top_spawn_area = pygame.Vector2(random.randint(0, display_info.current_w), 0 - enemy_img.height)
        bottom_spawn_area = pygame.Vector2(random.randint(0, display_info.current_w), display_info.current_h + enemy_img.height)
        list_of_pos = [left_spawn_area, right_spawn_area, top_spawn_area, bottom_spawn_area]
        ran_pos = list_of_pos[random.randint(0, len(list_of_pos)- 1)]
        return ran_pos

def handle_input():
    global state
    key_hold = pygame.key.get_pressed()
    key_press = pygame.key.get_just_pressed()
    if state == RUNNING:
        # shooting
        if key_hold[pygame.K_SPACE]:
            default_gun.shoot()
            default_gun.is_holding = True

        if key_press[pygame.K_r]:
            default_gun.reload()

    #always work...
    if key_press[pygame.K_RETURN]:
        state = EXIT

    #pause/unpause game
    if key_press[pygame.K_ESCAPE]:
        if state == RUNNING:
            state = PAUSED
        else:
            state = RUNNING

class Player:
    def __init__(self):
        self.health = 100
        self.speed = 4

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

    def add_speed(self):
        key_hold = pygame.key.get_pressed()

        self.move.x = (key_hold[pygame.K_d] - key_hold[pygame.K_a])
        self.move.y = (key_hold[pygame.K_s] - key_hold[pygame.K_w])

    def move_pos(self):
        if self.move.x != 0 and self.move.y != 0:
            self.move.x *= .75
            self.move.y *= .75
        self.pos.x += self.move.x * self.speed
        self.pos.y += self.move.y * self.speed
        self.rect.center = (self.pos.x, self.pos.y)

    def collision(self):
        global player_points
        global player_coins
        for item in items_list:
            collided = self.rect.colliderect(item)
            if collided:
                items_list.remove(item)
                player_points += 9
                player_coins += 10

        half_width = self.rect.width / 2
        half_height = self.rect.height / 2

        if self.pos.x - half_width < 0:
            self.pos.x = half_width

        elif self.pos.x + half_width > display_info.current_w:
            self.pos.x = display_info.current_w - half_width

        elif self.pos.y - half_height < 0:
            self.pos.y = half_height

        elif self.pos.y + half_height > display_info.current_h:
            self.pos.y = display_info.current_h - half_height

    def draw(self):
        pygame.draw.rect(screen, 'red', self.rect, 5)
        screen.blit(self.current_image, (
        self.rect.centerx - self.current_image.get_width() / 2, self.rect.centery - self.current_image.get_height() / 2))

    #def die(self):
        #if self.health <= 0:

    def manager(self):
        if self.move:
            self.current_state = 'shooting'
            self.current_original_image = self.original_shooting_img
            self.current_image = self.shooting_img
        else:
            self.current_state = 'idle'
            self.current_original_image = self.original_idle_img
            self.current_image = self.idle_img
        self.add_speed()
        self.move_pos()
        self.current_image = pygame.transform.rotate(self.current_image, rotate_img(get_mouse_pos(), self.rect.center, IMAGE_OFFSET))
        self.draw()
        self.collision()

class Gun:
    def __init__(self):
        self.magazine_capacity = 20
        self.ammo = self.magazine_capacity

        self.is_holding = False
        self.has_fired = False
        self.is_shooting = False
        self.start_shoot_time = None
        self.time_between_shot = 150.00

        self.is_reloading = False
        self.start_reload_time = None
        self.reload_time = 2000.0

    def shoot(self):
        if self.ammo <= 0:
            self.is_reloading = True
            self.reload()
            return
        self.is_shooting = True
        self.start_shoot_time = pygame.time.get_ticks()

    def shooting(self):
        if self.has_fired:
            elapsed_time = pygame.time.get_ticks() - self.start_shoot_time
            if elapsed_time >= self.time_between_shot:
                if self.is_holding:
                    self.ammo -= 1
                    bullet_list.append(Bullet())
                    self.is_shooting = False
                    self.shoot()
                else:
                    self.is_shooting = False
                    self.has_fired = False
        else:
            self.ammo -= 1
            bullet_list.append(Bullet())
            self.has_fired = True

    def reload(self):
        default_gun.is_reloading = True
        self.start_reload_time = pygame.time.get_ticks()

    def reloading(self):
        elapsed_time = pygame.time.get_ticks() - self.start_reload_time
        if elapsed_time >= self.reload_time:
            self.is_reloading = False
            self.ammo = self.magazine_capacity
            if self.is_holding:
                self.shoot()

    def manager(self):
        if self.is_shooting:
            self.shooting()

        if self.is_reloading:
            self.reloading()

        for bullet in bullet_list:
            if bullet.is_alive:
                Bullet.manager(bullet)
            else:
                bullet_list.remove(bullet)

class Bullet:
    def __init__(self):
        self.is_alive = True
        self.speed = 25
        self.damage = 25

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
        #enemy base stats
        self.idle, self.chase, self.attack = 0, 1, 2
        self.state = self.chase
        self.is_alive = True
        self.health = 100
        self.speed = 3
        self.target_distance = 70

        self.original_image = enemy_img
        self.image = self.original_image

        self.current_original_image = self.original_image
        self.current_image = self.image

        self.current_pos = outer_spawn_pos()
        self.rect = pygame.Rect(self.current_pos.x, self.current_pos.y, self.original_image.get_width(), self.original_image.get_height())

    def rot_enemy(self, target_pos):
        direction = pygame.Vector2(target_pos) - pygame.Vector2(self.rect.center)
        angle = math.degrees(math.atan2(direction.y, direction.x))

        #convert img rot to face towards player with offset since wrong front plane
        offset = -90
        self.image = pygame.transform.rotate(self.original_image, -angle + offset)

    def move_towards(self, target_pos):
            current_pos = pygame.math.Vector2(self.rect.centerx, self.rect.centery)
            direction = target_pos - current_pos

            try:
                direction.normalize_ip()
            except ValueError:
                return "Cant normalize vector of zero"

            #self.rot_enemy(target_pos)
            self.rect.center += direction * self.speed

    def draw(self):
        pygame.draw.rect(screen, 'red', self.rect, 5) #border
        screen.blit(self.current_image, (self.rect.centerx - self.current_image.get_width() / 2, self.rect.centery - self.current_image.get_height() / 2))

    def collision(self):
        global player_points
        global player_coins

        for target in bullet_list:
            collided = self.rect.colliderect(target)
            if collided:
                self.health -= target.damage
                #Get points per hit, buying items or doing something
                player_points += 13
                #Get coins after killing a enemy
                player_coins += 1
                bullet_list.remove(target)

    def enemy_covid(self):
        #global covid
        for enemy in wave_system.all_enemies:
            self_pos = pygame.Vector2(self.rect.centerx, self.rect.centery)
            enemy_pos = pygame.Vector2(enemy.rect.centerx, enemy.rect.centery)
            if self_pos == enemy_pos:
                continue
            else:
                ...#covid = pygame.math.Vector2.distance_to(self_pos, enemy_pos)

    def manager(self, target_pos):
        dist = pygame.math.Vector2.distance_to(pygame.Vector2(self.rect.centerx, self.rect.centery), target_pos)
        if dist < self.target_distance:
            self.state = self.attack
        else:
            self.state = self.chase

        if self.health <= 0:
            self.is_alive = False

        self.current_image = pygame.transform.rotate(self.original_image, rotate_img(target_pos, self.rect.center, IMAGE_OFFSET))
        self.draw()
        self.collision()

        if self.state == self.chase:
            self.move_towards(target_pos)
        elif self.state == self.attack:
            ...#attack

#region -- item classes --
class Item:
    def __init__(self):
        self.pos = random_pos()
        self.coin_img = coin_img
        self.rect = pygame.Rect(self.pos.x, self.pos.y, self.coin_img.get_width(), self.coin_img.get_height())

class Coins(Item):
    def draw(self):
        pygame.draw.rect(screen, 'red', self.rect, 1)
        screen.blit(self.coin_img, self.pos)

class Wood(Item):
    def draw(self):
        pygame.draw.rect(screen, 'red', self.rect, 1)
        screen.blit(self.coin_img, self.pos)

class Stone(Item):
    def draw(self):
        pygame.draw.rect(screen, 'red', self.rect, 1)
        screen.blit(self.coin_img, self.pos)

for _ in range(20):
    items_list.append(Coins())

def draw_items():
    for item in items_list:
        item.draw()
#endregion

#region -- wave system --
class WaveSystem:
    def __init__(self):
        self.STARTED, self.PAUSED, self.ENDED = 0, 1, 2
        self.state = None

        self.wave_started = False
        self.start_time = 2000.0
        self.round_ended = None
        self.start_amount = 3
        self.all_enemies = []


        self.wave = 0
        self.max_amount = 5
        self.amount_left = self.max_amount
        self.amount_spawned = 0

        self.current_count = 0
        self.current_max = 3

        self.start_amount_increase = 3
        self.current_max_increase = 3
        self.max_amount_increase = 5


    def spawn_enemy(self, enemy_amount):
        if self.amount_spawned >= self.max_amount:
            return
        else:
            for _ in range(enemy_amount):
                self.amount_spawned += 1
                self.all_enemies.append(Enemy())

    def round(self, player_pos):
        global player_kill_count
        global player_points
        global player_coins

        if self.current_count < self.current_max:
            self.spawn_enemy(1)

        for enemy in self.all_enemies:
            if enemy.is_alive:
                Enemy.manager(enemy, player_pos)
            else:
                player_kill_count += 1
                player_points += 55
                player_coins += 15
                self.amount_left -=1
                self.all_enemies.remove(enemy)

    def end_round(self):
            self.state = self.PAUSED
            self.wave_started = False
            self.wave += 1
            self.max_amount += self.max_amount_increase
            self.amount_left = self.max_amount
            self.start_amount += self.start_amount_increase
            self.current_max += self.current_max_increase
            self.amount_spawned = 0
            self.round_ended = pygame.time.get_ticks()


    def manager(self, player_pos):
        self.current_count = len(self.all_enemies)

        #start waves, change to player press button start
        if pygame.key.get_just_pressed()[pygame.K_l] and not self.state:
            self.state = self.STARTED

        #start wave x time after last wave
        elif self.state == self.PAUSED:
            elapsed_time = pygame.time.get_ticks() - self.round_ended
            if elapsed_time >= self.start_time:
                self.state = self.STARTED

        #wave started
        elif self.state == self.STARTED:

            if self.wave_started:
                self.round(player_pos)
            else:
                self.wave_started = True
                self.spawn_enemy(self.start_amount)

            if self.amount_left <= 0:
                self.state = self.ENDED

        #wave ended
        elif self.state == self.ENDED:
            self.end_round()


#endregion

#endregion

#region --- initialization ---
#region -- initializing enemies --
wave_system = WaveSystem()

#endregion

#region -- initializing player --
player = Player()
default_gun = Gun()
#endregion
#endregion

#region --- Main loop ---
while True:
    #region -- event loop --
    for event in pygame.event.get():
        #loops through events until no events left or break then loop through current state
        if event.type == pygame.QUIT:
            game_main = False
            break
        elif event.type == pygame.KEYDOWN:
            handle_input()
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                default_gun.is_holding = False
            #if KEYUP_u
            player.move.x = 0
            player.move.y = 0
        elif event.type == TIMER_EVENT:
            if frame == 3:
                frame = 0
            else: frame += 1
    #endregion
    else:
        if state == START:
            ...
        elif state == RUNNING:
            screen.fill('green')

            #region --object update--
            player.manager()
            default_gun.manager()
            draw_items()
            #endregion

            #region --enemy wave system--
            wave_system.manager(pygame.Vector2(player.rect.centerx, player.rect.centery))
            #endregion

            #region --UI update--
            mousex, mousey = get_mouse_pos()
            UI_mouse_pos.rect = pygame.Rect(mousex, mousey, 200, 120)
            UI_items.rect = pygame.Rect(0, 0, 150, 200)
            UI_items.set_text(f'Time: {convert_time()}\nKills: {player_kill_count}\npoints: {player_points}\ncoins: {player_coins}\n\nmagazine: {default_gun.ammo}')
            UI_mouse_pos.set_text(f'playerpos: {player.rect.centerx},{player.rect.centery}\nmousepos: {mousex}, {mousey}\ndistance: {get_direction(get_mouse_pos(), player.rect.center)}')
            UI_Manager.update(clock.tick(60)/1000.0)
            UI_Manager.draw_ui(screen)
            #endregion

            #region Refresh screen and set fps
            pygame.display.flip()
            clock.tick(60)
            #endregion
        if state == PAUSED:
            ...
            #paused state
        if state == EXIT:
            print(f'exit game')
            break
        continue
#endregion

#Quit if main loop breaks
pygame.quit()