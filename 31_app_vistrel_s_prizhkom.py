import math
import arcade
import arcade.sound

SCREEN_TITLE = "Использование PyMunk"
SPRITE_IMAGE_SIZE = 128
SPRITE_SCALING_PLAYER = 0.3
SPRITE_SCALING_TILES = 0.3
SPRITE_SIZE = int(SPRITE_IMAGE_SIZE * SPRITE_SCALING_PLAYER)
SCREEN_GRID_WIDTH = 25
SCREEN_GRID_HEIGHT = 15
SCREEN_WIDTH = SPRITE_SIZE * SCREEN_GRID_WIDTH
SCREEN_HEIGHT = SPRITE_SIZE * SCREEN_GRID_HEIGHT
HEALTH = 100
GRAVITY = 25

PLAYER_JUMP_FORCE = 35000
DEFAULT_DAMPING = 1.0
PLAYER_DAMPING = 0.4
PLAYER_FRICTION = 1.0
WALL_FRICTION = 99
DYNAMIC_ITEM_FRICTION = 0.6
PLAYER_MASS = 2.0
PLAYER_MAX_HORIZONTAL_SPEED = 200
PLAYER_MAX_VERTICAL_SPEED = 1600
PLAYER_MOVE_FORCE_ON_GROUND = 9999
DEAD_ZONE = 0.1
RIGHT_FACING = 0
LEFT_FACING = 1
DISTANCE_TO_CHANGE_TEXTURE = 5
BULLET_MOVE_FORCE = 4500
BULLET_MASS = 0.1
BULLET_GRAVITY = 300


class BulletSprite(arcade.SpriteSolidColor):
    def pymunk_moved(self, physics_engine, dx, dy, d_angle):
        if self.center_y < -100:
            self.remove_from_sprite_lists()


class PlayerSprite(arcade.Sprite):
   def __init__(self):
       super().__init__()

       self.scale = SPRITE_SCALING_PLAYER

       main_path = ":resources:images/animated_characters/female_person/femalePerson"

       self.idle_texture_pair = arcade.load_texture_pair(f"{main_path}_idle.png")
       self.jump_texture_pair = arcade.load_texture_pair(f"{main_path}_jump.png")
       self.fall_texture_pair = arcade.load_texture_pair(f"{main_path}_fall.png")

       self.walk_textures = []
       for i in range(8):
           texture = arcade.load_texture_pair(f"{main_path}_walk{i}.png")
           self.walk_textures.append(texture)

       self.texture = self.idle_texture_pair[0]

       self.hit_box = self.texture.hit_box_points
       self.character_face_direction = RIGHT_FACING
       self.cur_texture = 0
       self.x_odometer = 0

   def pymunk_moved(self, physics_engine, dx, dy, d_angle):
       if dx < -DEAD_ZONE and self.character_face_direction == RIGHT_FACING:
           self.character_face_direction = LEFT_FACING
       elif dx > DEAD_ZONE and self.character_face_direction == LEFT_FACING:
           self.character_face_direction = RIGHT_FACING

       is_on_ground = physics_engine.is_on_ground(self)

       self.x_odometer += dx

       if not is_on_ground:
           if dy > DEAD_ZONE:
               self.texture = self.jump_texture_pair[self.character_face_direction]
               return
           elif dy < -DEAD_ZONE:
               self.texture = self.fall_texture_pair[self.character_face_direction]
               return

       if abs(dx) <= DEAD_ZONE:
           self.texture = self.idle_texture_pair[self.character_face_direction]
           return

       if abs(self.x_odometer) > DISTANCE_TO_CHANGE_TEXTURE:

           self.x_odometer = 0

           self.cur_texture += 1
           if self.cur_texture > 7:
               self.cur_texture = 0
           self.texture = self.walk_textures[self.cur_texture][self.character_face_direction]


class GameWindow(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        self.player_sprite = None
        self.player_list = None
        self.wall_list = None
        self.bullet_list = None
        self.item_list = None
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False  # <-- Добавлено для прыжка
        arcade.set_background_color(arcade.color.AMAZON)
        self.physics_engine = None
        self.moving_sprites_list = None

        self.background_music = arcade.sound.load_sound('barbariki.mp3')
        arcade.sound.play_sound(self.background_music, 0.5)

    def check_game_over(self):
        """Проверка условий победы и поражения"""
        if len(self.item_list) == 0:
            self.end_game('Победа')

    def end_game(self, message):
        """Закончить игру сообщением"""
        print(message)
        arcade.close_window()


    def setup(self):
       self.player_list = arcade.SpriteList()
       self.bullet_list = arcade.SpriteList()
       map_name = ":resources:/tiled_maps/pymunk_test_map.json"
       tile_map = arcade.load_tilemap(map_name, SPRITE_SCALING_TILES)
       print(tile_map.sprite_lists)
       self.wall_list = tile_map.sprite_lists["Platforms"]
       self.item_list = tile_map.sprite_lists["Dynamic Items"]
       self.player_sprite = PlayerSprite()

       self.player_sprite.center_x = SPRITE_SIZE + SPRITE_SIZE / 2
       self.player_sprite.center_y = SPRITE_SIZE + SPRITE_SIZE / 2
       self.player_list.append(self.player_sprite)
       damping = DEFAULT_DAMPING
       gravity = (0, -GRAVITY)
       self.physics_engine = arcade.PymunkPhysicsEngine(damping=damping,
                                                        gravity=gravity)
       self.physics_engine.add_sprite(self.player_sprite,
                                      friction=PLAYER_FRICTION,
                                      mass=PLAYER_MASS,
                                      moment=arcade.PymunkPhysicsEngine.MOMENT_INF,
                                      collision_type="player",
                                      max_horizontal_velocity=PLAYER_MAX_HORIZONTAL_SPEED,
                                      max_vertical_velocity=PLAYER_MAX_VERTICAL_SPEED)
       self.physics_engine.add_sprite_list(self.wall_list,
                                           friction=WALL_FRICTION,
                                           collision_type="wall",
                                           body_type=arcade.PymunkPhysicsEngine.STATIC)
       self.physics_engine.add_sprite_list(self.item_list,
                                           friction=DYNAMIC_ITEM_FRICTION,
                                           collision_type="item")

       def wall_hit_handler(bullet_sprite, _wall_sprite, _arbiter, _space, _data):
           bullet_sprite.remove_from_sprite_lists()

       self.physics_engine.add_collision_handler("bullet", "wall", post_handler=wall_hit_handler)

       def item_hit_handler(bullet_sprite, item_sprite, _arbiter, _space, _data):
           bullet_sprite.remove_from_sprite_lists()
           item_sprite.remove_from_sprite_lists()

       self.physics_engine.add_collision_handler("bullet", "item", post_handler=item_hit_handler)
       self.moving_sprites_list = tile_map.sprite_lists['Moving Platforms']
       self.physics_engine.add_sprite_list(self.moving_sprites_list,
                                           body_type=arcade.PymunkPhysicsEngine.KINEMATIC)



       def player_item_collision_handler(player_sprite, item_sprite, _arbiter, _space, _data):
           item_sprite.remove_from_sprite_lists()
           self.end_game('Поражение')

       self.physics_engine.add_collision_handler('player', 'item', post_handler=player_item_collision_handler)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.LEFT:
            self.left_pressed = True
        elif key == arcade.key.RIGHT:
            self.right_pressed = True
        elif key == arcade.key.UP:  # <-- Добавлено для прыжка
            self.up_pressed = True


    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False
        elif key == arcade.key.UP:  # <-- Добавлено для прыжка
            self.up_pressed = False

    def on_update(self, delta_time):
        if self.left_pressed and not self.right_pressed:
            force = (-PLAYER_MOVE_FORCE_ON_GROUND, 0)
            self.physics_engine.apply_force(self.player_sprite, force)
            self.physics_engine.set_friction(self.player_sprite, 0)
        elif self.right_pressed and not self.left_pressed:
            force = (PLAYER_MOVE_FORCE_ON_GROUND, 0)
            self.physics_engine.apply_force(self.player_sprite, force)
            self.physics_engine.set_friction(self.player_sprite, 0)
        else:
            self.physics_engine.set_friction(self.player_sprite, 1.0)

        if self.up_pressed and self.physics_engine.is_on_ground(self.player_sprite):
            force = (0, PLAYER_JUMP_FORCE)
            self.physics_engine.apply_force(self.player_sprite, force)
            self.up_pressed = False

        self.physics_engine.step()

        self.check_game_over()

    def on_draw(self):
       self.clear()
       self.wall_list.draw()
       self.item_list.draw()
       self.bullet_list.draw()
       self.player_list.draw()
       self.moving_sprites_list.draw()

    def on_mouse_press(self, x, y, button, modifiers):
       bullet = BulletSprite(20, 5, arcade.color.DARK_YELLOW)
       self.bullet_list.append(bullet)
       start_x = self.player_sprite.center_x
       start_y = self.player_sprite.center_y
       bullet.position = self.player_sprite.position

       dest_x = x
       dest_y = y

       x_diff = dest_x - start_x
       y_diff = dest_y - start_y
       angle = math.atan2(y_diff, x_diff)

       size = max(self.player_sprite.width, self.player_sprite.height) / 2

       bullet.center_x += size * math.cos(angle)
       bullet.center_y += size * math.sin(angle)
       bullet.angle = math.degrees(angle)

       bullet_gravity = (0, -BULLET_GRAVITY)

       self.physics_engine.add_sprite(bullet,
                                      mass=BULLET_MASS,
                                      damping=1.0,
                                      friction=0.6,
                                      collision_type="bullet",
                                      gravity=bullet_gravity,
                                      elasticity=0.9)

       force = (BULLET_MOVE_FORCE, 0)
       print(self.bullet_list)
       self.physics_engine.apply_force(bullet, force)


def main():
   window = GameWindow(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
   window.setup()
   arcade.run()


if __name__ == "__main__":
   main()
