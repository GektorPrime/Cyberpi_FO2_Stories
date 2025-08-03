# latest. kina stable. skin swap takes 7-10s. crashes after 7 swaps.


import gc
import cyberpi  # type: ignore
import random
from time import sleep


# ---------------------------------------------------------
# Debug constants
# ---------------------------------------------------------
DEBUG = True
LOW_BATTERY_MAX = 15
LOW_BATTERY_MIN = 1
HUNGER = 69
HAPPINESS = 30
ENERGY = 30
HEALTH = 1
IS_AWAKE = True
IS_SICK = False
IS_RAD = False


# ---------------------------------------------------------
def _start_to_render():
    try:
        cyberpi.screen.enable_autorender()
        if DEBUG:
            print('autorender started...')
        sleep(0.05)
    except Exception as err:
        _handle_error(err, 'Start to Render')


def _stop_to_render():
    try:
        cyberpi.screen.disable_autorender()
        if DEBUG:
            print('autorender stopped...')
        sleep(0.05)
    except Exception as err:
        try:
            cyberpi.console.print('ERROR: ' + str(err))
        except Exception as err:
            print(err)


_stop_to_render()
# ---------------------------------------------------------


# ---------------------------------------------------------
# Globals
# ---------------------------------------------------------
game = None
# Constants
FILE_ACCESS_LOCK = False
BIN_ARRAY_CACHE = {}
VOLUME = 3
# INPUT_DELAY = 0.2
# GAME_LOOP_DELAY = 0.15
# DEATH_BLINK_INTERVAL = 0.6
# MESSAGE_SCREEN_TIMEOUT = 15
# WAKE_PROTECTION_MINUTES = 3

PIXEL_ARRAYS_BASE_PATH = 'fo2_stories_assets/pixel_arrays/'
PRELOAD_PIXEL_ARRAY_FILES_BIN = ['adv_pa_front_1.bin', 'adv_pa_front_2.bin',
                                 'adv_pa_back_1.bin', 'adv_pa_back_2.bin',
                                 'adv_pa_sleep_1.bin', 'adv_pa_sleep_2.bin', 'adv_pa_ground_1.bin',
                                 'f_dweller_front_1.bin', 'f_dweller_front_2.bin',
                                 'f_dweller_back_1.bin', 'f_dweller_back_2.bin',
                                 'f_dweller_sleep_1.bin', 'f_dweller_sleep_2.bin', 'dweller_dead_1.bin']
PIXEL_ARRAY_FILES_BIN = ['background_1.bin', 'background_2.bin', 'background_3.bin',
                         'bg3_grave_top.bin', 'bg3_coffin.bin',
                         'fire_1.bin', 'fire_2.bin', 'fire_3.bin', 'fire_4.bin'] + PRELOAD_PIXEL_ARRAY_FILES_BIN

# Colors (R, G, B tuples)
COLORS = {
    'red': (255, 0, 0),            # sick, rest, and battery_low
    'orange': (255, 50, 0),        # hungry
    'amber': (255, 176, 0),        # vacant
    'yellow': (255, 255, 0),       # vacant
    'screen_green': (48, 56, 43),  # background, curtain
    'console_green': (0, 128, 0),  # console font
    'green': (0, 255, 0),          # rad
    'cyan': (0, 255, 255),         # tired
    'blue': (0, 0, 50),            # sleeping
    'purple': (75, 0, 130),        # sad, depressed
    'magenta': (255, 0, 255),     # happy
    'pink': (225, 50, 100),        # content
    'white': (100, 100, 100),      # default for all unspecified states
    'black': (0, 0, 0),
}

# PipBoy face expressions
FACES = {
    'dead': '    q[X_X]p',
    'sick': '    q[@_@]p',
    'rad': '    q[*_*]p',
    'sleeping_1': '    q[z_z]p',
    'sleeping_2': '    q[Z_Z]p',
    'hungry_1': '    q[ioi]p',
    'hungry_2': '    q[iOi]p',
    'happy_1': '    q[^w^]p',
    'happy_2': '    q[^W^]p',
    'content_1': '    q[o_0]p',
    'content_2': '    q[0_o]p',
    'content_3': '    q[o_o]p',
    'content_4': '    q[0_0]p',
    'sad': '    q[T_T]p',
    'battery_low_1': '    q[+_-]p',
    'battery_low_2': '    q[-_+]p',
    'on_mission': '    q[>_<]p'
}

DEBUG_SPRITE = cyberpi.sprite()
DEBUG_SPRITE.set_align(align_point='top_left')
DEBUG_SPRITE.move_to(2, 2)


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------
def _debug_sprite_text(text):
    DEBUG_SPRITE.draw_text(text)


def _show_botton_left_label(text, size=16, position='bottom_left'):
    cyberpi.display.show_label(text, size, position)


def print_free_mem():
    text = 'Free mem:\n' + str(gc.mem_free()) + ' bytes\n\n\n\n'
    _show_botton_left_label(text)
    # cyberpi.console.println('Loading...')
    # cyberpi.console.println('Free mem:')
    # cyberpi.console.println(str(gc.mem_free()) + ' bytes')
    sleep(0.3)


def _load_cached_binary_array(file):
    array = BIN_ARRAY_CACHE.get(file)
    if array is None:
        raise RuntimeError('Missing cached binary for: ' + file)
    return array


def _load_file_binary_array(file):
    """
    Helper function to load binary array files
    """
    global FILE_ACCESS_LOCK
    while FILE_ACCESS_LOCK:
        sleep(0.1)
    FILE_ACCESS_LOCK = True
    f = None
    if FILE_ACCESS_LOCK:
        try:
            filepath = PIXEL_ARRAYS_BASE_PATH + file
            print('Attempting to open ' + filepath)
            f = open(filepath, 'rb')
            print('Opened:', file)
            # Read array length
            length_bytes = f.read(4)
            if len(length_bytes) != 4:
                return None
            length = int.from_bytes(length_bytes, 'little')
            array = []
            for _ in range(length):
                value_bytes = f.read(4)
                if len(value_bytes) != 4:
                    return None
                value = int.from_bytes(value_bytes, 'little')
                array.append(value)
            return array
        except Exception as e:
            raise RuntimeError('Error loading ' + file + ': ' + str(e))
        finally:
            print('Success. Returning array')
            if f:
                try:
                    f.close()
                    print('Closed:', file)
                except Exception as e:
                    print('Failed to close file:', e)
            FILE_ACCESS_LOCK = False
            gc.collect()
            print_free_mem()


def preload_bin_arrays():
    for file in PRELOAD_PIXEL_ARRAY_FILES_BIN:
        array = _load_file_binary_array(file)
        if array is None:
            raise RuntimeError('Failed to load: ' + file)
        BIN_ARRAY_CACHE[file] = array
    print('[INFO] All binary pixel arrays loaded into cache')


def _safe_screen_clear():
    try:
        cyberpi.console.clear()
        cyberpi.display.clear()
        if DEBUG:
            print('Console and display cleared...')
        sleep(0.05)
    except Exception as err:
        try:
            cyberpi.console.print('ERROR: ' + str(err))
        except Exception as err:
            print(err)


def _handle_error(error, context='Unknown'):
    """Global error handler that cleans screen and returns error text."""
    _stop_to_render()
    _safe_screen_clear()
    error_msg = 'ERROR [' + str(context) + ']: ' + str(error)
    try:
        cyberpi.console.print(error_msg)
    except Exception as err:
        print(err)
    return error_msg


def _safe_play_audio(sound_name):
    try:
        cyberpi.audio.play(sound_name)
        sleep(0.05)
    except Exception as err:
        _handle_error(err, 'Play Audio')


def _render_me():
    try:
        cyberpi.screen.render()
        sleep(0.05)
    except Exception as err:
        _handle_error(err, 'Manual Render')


# ---------------------------------------------------------
# Class definitions
# ---------------------------------------------------------
class SpriteFactory:
    """Generic factory class to load and manage game sprites."""

    def __init__(self): ...

    def create_sprites_from_bin_pixel_arrays(self, files, x=None, y=None):
        if isinstance(files, list):
            array = None
            for file in files:
                if file not in PIXEL_ARRAY_FILES_BIN:
                    raise ValueError(file + ' is not among registred files')
                else:
                    name = file.split('.')[0]
                    array = _load_file_binary_array(file)
                    if array is not None:
                        sprite = cyberpi.sprite()
                        sprite.draw_pixel(array, x, y)
                        sprite.hide()
                        setattr(self, name, sprite)
                        if DEBUG:
                            print("Pixel array loaded:", name)
                    else:
                        if DEBUG:
                            print("Failed to load array:", file)
            del array
            gc.collect()
            print('Free mem:', gc.mem_free())
            if DEBUG:
                print("Batch of pixel arrays loaded")
        else:
            raise ValueError('files should be a list of strings')

    def create_sprites_from_cached_pixel_arrays(self, files, x=None, y=None):
        if isinstance(files, list):
            print('Loading from cache: ' + str(files))
            array = None
            for file in files:
                if file not in PIXEL_ARRAY_FILES_BIN:
                    raise ValueError(str(file) + ' is not among registred files')
                else:
                    array = _load_cached_binary_array(file)
                    if array is not None:
                        sprite = cyberpi.sprite()
                        sprite.draw_pixel(array, x, y)
                        sprite.hide()
                        attr = file.split('.')[0]
                        setattr(self, attr, sprite)
            del array
            gc.collect()
            print('Free mem:', gc.mem_free())

    @staticmethod
    def _create_curtains_128x128_sprite_array():
        """Create transparent array safely"""
        try:
            array = []
            for _ in range(16384):
                array.append(0x008000)
            if DEBUG:
                print('Transparent array created')
            gc.collect()
            return array
        except Exception as err:
            if DEBUG:
                print('Transparent array creation error:', err)
            return None

    def hide_all(self):
        """Hide all sprites attached as attributes."""
        for name, sprite in self.__dict__.items():
            # Skip internal tracking variables
            if name.startswith('_'):
                continue
            if sprite is not None and hasattr(sprite, 'hide') and callable(sprite.hide):
                try:
                    sprite.hide()
                except Exception as err:
                    if DEBUG:
                        print('Error hiding sprite', name + ':', str(err))

    def show_all(self):
        """Show all sprites attached as attributes."""
        for name, sprite in self.__dict__.items():
            # Skip internal tracking variables
            if name.startswith('_'):
                continue
            if sprite is not None and hasattr(sprite, 'show') and callable(sprite.show):
                try:
                    sprite.show()
                except Exception as err:
                    if DEBUG:
                        print('Error showing sprite', name + ':', str(err))

    def move_all_to(self, x, y):
        """Move all sprites to a specific position."""
        for name, sprite in self.__dict__.items():
            # Skip internal tracking variables
            if name.startswith('_'):
                continue
            if sprite is not None and hasattr(sprite, 'move_to') and callable(sprite.move_to):
                try:
                    sprite.move_to(x, y)
                except Exception as err:
                    if DEBUG:
                        print('Error moving sprite', name + ':', str(err))

    def clean_sprite_factory(self):
        """Clean up all sprites, attributes and free memory."""
        for name, sprite in self.__dict__.items():
            # Skip internal tracking variables
            if name.startswith('_'):
                continue
            if sprite is not None and hasattr(sprite, 'delete') and callable(sprite.delete):
                print('deleting', sprite)
                sprite.delete()
                print('deleted')
            delattr(self, name)
            print('attr: ' + name + ' deleted')
        if DEBUG:
            print('SpriteFactory cleaned up')
        gc.collect()
        sleep(0.1)

    def get_sprite_names(self):
        """Get list of all loaded sprite names."""
        return [name for name in self.__dict__.keys() if not name.startswith('_')]


class SkinFactory(SpriteFactory):  # self.skin
    def __init__(self):
        super().__init__()
        self.front_1 = None
        self.front_2 = None
        self.back_1 = None
        self.back_2 = None
        self.sleep_1 = None
        self.sleep_2 = None
        self.dead = None
        self.standing_sprites_front = None
        self.standing_sprites_back = None
        self.standing_sprites = None
        self.sleeping_sprites = None

    def _create_sprites(self):
        self.front_1 = cyberpi.sprite()
        self.front_2 = cyberpi.sprite()
        self.back_1 = cyberpi.sprite()
        self.back_2 = cyberpi.sprite()
        self.sleep_1 = cyberpi.sprite()
        self.sleep_2 = cyberpi.sprite()
        self.dead = cyberpi.sprite()

    def draw_skin_pixels(self, files, x=None, y=None):
        if isinstance(files, list):
            print('Loading from cache: ' + str(files))
            for file in files:
                if file not in PIXEL_ARRAY_FILES_BIN:
                    raise ValueError(str(file) + ' is not among registred files')
                else:
                    array = _load_cached_binary_array(file)
                    if 'front_1' in file:
                        self.front_1.draw_pixel(array, x, y)
                        self.front_1.hide()
                    elif 'front_2' in file:
                        self.front_2.draw_pixel(array, x, y)
                        self.front_2.hide()
                    elif 'back_1' in file:
                        self.back_1.draw_pixel(array, x, y)
                        self.back_1.hide()
                    elif 'back_2' in file:
                        self.back_2.draw_pixel(array, x, y)
                        self.back_2.hide()
                    elif 'sleep_1' in file:
                        self.sleep_1.draw_pixel(array, x, y)
                        self.sleep_1.hide()
                    elif 'sleep_2' in file:
                        self.sleep_2.draw_pixel(array, x, y)
                        self.sleep_2.hide()
                    elif 'dead' in file or 'ground' in file:
                        self.dead.draw_pixel(array, x, y)
                        self.dead.hide()
                    else:
                        raise ValueError(file + ' is not a legit skin part')
            gc.collect()
            print('Free mem:', gc.mem_free())

    def _setup_sprite_groups(self):
        """Organize sprites into logical groups"""
        self.standing_sprites_front = [self.front_1, self.front_2]
        self.standing_sprites_back = [self.back_1, self.back_2]
        self.sleeping_sprites = [self.sleep_1, self.sleep_2]
        self.standing_sprites = self.standing_sprites_front

    def _position_sprites(self):
        """Set initial positions for sprites"""
        for sprite in self.standing_sprites:
            if sprite is not None:
                sprite.move_to(65, 64)
        for sprite in self.sleeping_sprites:
            if sprite is not None:
                sprite.set_align(align_point='mid_left')
                sprite.move_to(13, 78)

    def load_vault_suit_skin(self):
        self.draw_skin_pixels(['f_dweller_front_1.bin', 'f_dweller_front_2.bin',
                               'f_dweller_back_1.bin', 'f_dweller_back_2.bin'], 18, 60)
        self.draw_skin_pixels(['f_dweller_sleep_1.bin', 'f_dweller_sleep_2.bin'], 55, 32)
        self.draw_skin_pixels(['dweller_dead_1.bin'], 67, 41)
        return True

    def load_adv_power_armor_skin(self):
        self.draw_skin_pixels(['adv_pa_front_1.bin', 'adv_pa_front_2.bin',
                               'adv_pa_back_1.bin', 'adv_pa_back_2.bin'], 40, 76)
        self.draw_skin_pixels(['adv_pa_sleep_1.bin', 'adv_pa_sleep_2.bin'], 68, 44)
        self.draw_skin_pixels(['adv_pa_ground_1.bin'], 72, 45)
        return True

    def load_raider_armor_skin(self):
        pass


class VaultDweller:
    """Represents the virtual character with stats and behaviors."""

    def __init__(self, name='Cyber'):
        self.name = name
        self.age = 0
        self.hunger = HUNGER if DEBUG else 0
        self.happiness = HAPPINESS if DEBUG else 50
        self.energy = ENERGY if DEBUG else 80
        self.health = HEALTH if DEBUG else 100
        self.is_alive = True
        self.is_awake = IS_AWAKE if DEBUG else True
        self.is_sick = IS_SICK if DEBUG else False
        self.is_rad = IS_RAD if DEBUG else False
        self.sick_start_time = 0
        self.rad_start_time = 0
        self.x_direction = 'east'
        self.y_direction = 'south'
        self._is_soul_mirrored = False
        # concept for the skin class
        self.skin = SkinFactory()
        self.current_skin_type = None
        self._is_changing_skin = False
        if DEBUG:
            print('VaultDweller initiated')

    def load_skin(self, skin_type):
        """Load a specific skin type"""
        self.skin._create_sprites()
        self.skin._setup_sprite_groups()
        self.skin._position_sprites()
        self.change_skin(skin_type)

    def change_skin(self, new_skin_type):
        """Change to a different skin"""
        self._is_changing_skin = True
        if new_skin_type != self.current_skin_type:
            self._is_soul_mirrored = False
            if new_skin_type == 'vault_suit':
                if DEBUG:
                    print('Loading skin ' + new_skin_type)
                changed = self.skin.load_vault_suit_skin()
                if changed:
                    self._is_changing_skin = False
            elif new_skin_type == 'adv_power_armor':
                if DEBUG:
                    print('Loading skin ' + new_skin_type)
                changed = self.skin.load_adv_power_armor_skin()
                if changed:
                    self._is_changing_skin = False
            elif new_skin_type == 'raider_armor':
                if DEBUG:
                    print('Loading skin ' + new_skin_type)
                changed = self.skin.load_raider_armor_skin()
                if changed:
                    self._is_changing_skin = False
            else:
                raise ValueError('Unknown skin type: ' + new_skin_type)
            self.current_skin_type = new_skin_type
            if DEBUG:
                print('Changed skin from ' + self.current_skin_type + ' to ' + new_skin_type)

    def set_skin_direction(self):
        if DEBUG:
            pass
        try:
            # First handle north/south sprite selection
            if self.y_direction == 'north':
                if self.skin.standing_sprites is not self.skin.standing_sprites_back:
                    for sprite in self.skin.standing_sprites_front:
                        if sprite is not None:
                            sprite.hide()
                    self.skin.standing_sprites = self.skin.standing_sprites_back
            elif self.y_direction == 'south':
                if self.skin.standing_sprites is not self.skin.standing_sprites_front:
                    for sprite in self.skin.standing_sprites_back:
                        if sprite is not None:
                            sprite.hide()
                    self.skin.standing_sprites = self.skin.standing_sprites_front
            else:
                raise ValueError('Invalid y_direction: ' + str(self.y_direction))
            # Collect all sprites that need direction updates
            sprites_to_update = []
            for sprite_list in [self.skin.sleeping_sprites,
                                self.skin.standing_sprites_front, self.skin.standing_sprites_back]:
                for sprite in sprite_list:
                    if sprite is not None:
                        sprites_to_update.append(sprite)
            # Handling west/east directions
            if self.x_direction == 'west':
                if not self._is_soul_mirrored:
                    # _stop_to_render()
                    for sprite in sprites_to_update:
                        if sprite is not None:
                            sprite.mirror('x')
                    for sprite in self.skin.sleeping_sprites:
                        if sprite is not None:
                            sprite.set_align(align_point='mid_right')
                            sprite.move_to(115, 78)
                    sleep(0.01)
                    # _start_to_render()
                    self._is_soul_mirrored = True
            elif self.x_direction == 'east':
                if self._is_soul_mirrored:
                    # _stop_to_render()
                    for sprite in sprites_to_update:
                        if sprite is not None:
                            sprite.mirror('x')
                    for sprite in self.skin.sleeping_sprites:
                        if sprite is not None:
                            sprite.set_align(align_point='mid_left')
                            sprite.move_to(13, 78)
                    sleep(0.01)
                    # _start_to_render()
                    self._is_soul_mirrored = False
            else:
                raise ValueError('Invalid x_direction: ' + str(self.x_direction))
        except Exception as err:
            _handle_error(err, 'Set Dweller\'s Direction')


class PipBoy:
    """Represents dweller's personal information processor interface."""

    def __init__(self):
        self.dweller = VaultDweller()
        self.current_screen = None
        self.screen_delimiter = '-'*16 + '\n'
        self.low_battery_min = LOW_BATTERY_MIN if DEBUG else 0
        self.battery_level = cyberpi.get_battery()
        if self.battery_level > self.low_battery_min:
            self.is_battery_low = self.battery_level <= LOW_BATTERY_MAX
        else:
            self.is_battery_low = True
        if DEBUG:
            print('PipBoy initiated')

    def get_mood(self):
        """Get current mood based on stats."""
        if self.is_battery_low and self.battery_level > self.low_battery_min:
            return 'CHARGING'
        if self.dweller.is_sick and self.dweller.is_rad:
            # Show whichever occurred first
            if self.dweller.sick_start_time <= self.dweller.rad_start_time:
                return 'SICK'
            else:
                return 'RAD'
        elif self.dweller.is_sick:
            return 'SICK'
        elif self.dweller.is_rad:
            return 'RAD'
        if not self.dweller.is_awake:
            return 'SLEEPING'
        if self.dweller.hunger >= 70:
            return 'HUNGRY'
        if self.dweller.happiness > 80:
            return 'HAPPY'
        elif self.dweller.happiness > 60:
            return 'CONTENT'
        elif self.dweller.happiness > 40:
            return 'OKAY'
        elif self.dweller.happiness > 25:
            return 'SAD'
        else:
            return 'DEPRESSED'

    def open(self):
        self.display_main()

    def display_main(self):
        """Display character face and status."""
        _safe_screen_clear()
        self.current_screen = 'main'
        if not self.dweller.is_alive:
            face = FACES['dead']
            status = 'DEAD'
            tooltip = 'B:GAME OVER'
        elif self.is_battery_low and self.battery_level > self.low_battery_min:
            faces = [FACES['battery_low_1'], FACES['battery_low_2']]
            face = random.choice(faces)
            status = 'CHRGE'
            tooltip = 'B:MENU A:Back'
        elif self.dweller.is_sick:
            face = FACES['sick']
            status = 'SICK'
            tooltip = 'B:MENU A:Back'
        elif self.dweller.is_rad:
            face = FACES['rad']
            status = 'RAD'
            tooltip = 'B:MENU A:Back'
        elif not self.dweller.is_awake:
            faces = [FACES['sleeping_1'], FACES['sleeping_2']]
            face = random.choice(faces)
            status = 'SLEEP'
            tooltip = 'B:MENU A:Back'
        elif self.get_mood() == "HUNGRY":
            faces = [FACES['hungry_1'], FACES['hungry_2']]
            face = random.choice(faces)
            status = 'HNGRY'
            tooltip = 'B:MENU A:Back'
        elif self.get_mood() == 'HAPPY':
            faces = [FACES['happy_1'], FACES['happy_2']]
            face = random.choice(faces)
            status = 'HAPPY'
            tooltip = 'B:MENU A:Back'
        elif self.get_mood() in ['CONTENT', 'OKAY']:
            faces = [FACES['content_1'], FACES['content_2'], FACES['content_3'], FACES['content_4']]
            face = random.choice(faces)
            status = 'OKAY'
            tooltip = 'B:MENU A:Back'
        else:
            face = FACES['sad']
            status = 'SAD'
            tooltip = 'B:MENU A:Back'

        name = '[DBUG]' if DEBUG else self.dweller.name
        frame = (
            face + '\n' + self.screen_delimiter +
            'Status:\n  Name:\n   Age: ' +
            '\n' + self.screen_delimiter + tooltip
        )
        _show_botton_left_label(frame)
        _safe_play_audio('prompt-tone')
        cyberpi.console.println(' ')
        cyberpi.console.println(' ')
        cyberpi.console.println(' ' * 7 + status)
        cyberpi.console.println(' ' * 7 + name)
        cyberpi.console.println(' ' * 7 + str(self.dweller.age))

    def display_stats(self):
        _safe_screen_clear()
        self.current_screen = 'stats'
        debug_status = ' [DBUG]' if DEBUG else ''
        frame = (
            '\n' + self.screen_delimiter +
            'Health:' + '     %' + '\nHunger:' + '     %' +
            '\n Happy:' + '     %' + '\nEnergy:' + '     %' +
            '\n' + self.screen_delimiter + 'A:Back' + debug_status
        )
        _show_botton_left_label(frame)
        _safe_play_audio('prompt-tone')
        cyberpi.console.println(' ')
        cyberpi.console.println(' ' * 8 + str(self.dweller.health))
        cyberpi.console.println(' ' * 8 + str(self.dweller.hunger))
        cyberpi.console.println(' ' * 8 + str(self.dweller.happiness))
        cyberpi.console.println(' ' * 8 + str(self.dweller.energy))

    def display_change_skin_menu(self):
        _safe_screen_clear()
        self.current_screen = 'change_skin_menu'
        frame = (
            '\n' + self.screen_delimiter +
            '\n\n\n' +
            '\n' + self.screen_delimiter + 'A:Back B:Change'
        )
        _show_botton_left_label(frame)
        _safe_play_audio('prompt-tone')
        cyberpi.console.println(' ')
        cyberpi.console.println(self.dweller.current_skin_type)
        cyberpi.console.println('Free:' + str(gc.mem_free()))
        cyberpi.console.println('Alloc:' + str(gc.mem_alloc()))

    def display_wait(self):
        _safe_screen_clear()
        self.current_screen = 'wait'
        frame = (
            '\n' + self.screen_delimiter +
            '\n\n\n' +
            '\n' + self.screen_delimiter + 'WAIT...'
        )
        _show_botton_left_label(frame)
        _safe_play_audio('prompt-tone')
        cyberpi.console.println(' ')
        cyberpi.console.println('Action is in progress...')


class FO2GameWorld:
    """Main game class that manages the game world, it's state and interactions."""

    def __init__(self):
        self._is_initiated = False
        self._is_over = False
        self.current_scene = None
        self.pip_boy = PipBoy()
        if DEBUG:
            print('FO2GameWorld initiated')

    def _setup_game_sprites(self):
        self.backgrounds = SpriteFactory()  # separate to Backgrounds class
        self.backgrounds.create_sprites_from_bin_pixel_arrays(['background_1.bin', 'background_2.bin',
                                                               'background_3.bin'], 128, 128)
        self.current_bg = random.choice([self.backgrounds.background_1, self.backgrounds.background_2,
                                         self.backgrounds.background_3])
        # hardcoding background_3 props for now:
        self.bg3_grave_top = cyberpi.sprite()
        self.bg3_grave_top.draw_pixel(_load_file_binary_array('bg3_grave_top.bin'), 86, 67)
        self.bg3_grave_top.set_align(align_point='top_right')
        self.bg3_grave_top.move_to(128, 0)
        self.bg3_coffin = cyberpi.sprite()
        self.bg3_coffin.draw_pixel(_load_file_binary_array('bg3_coffin.bin'), 58, 41)
        self.bg3_coffin.set_align(align_point='top_left')
        self.bg3_coffin.move_to(0, 12)
        self.pip_boy.dweller.load_skin('vault_suit')
        self.fire_barrel = SpriteFactory()  # separate to FireBarrel class
        self.fire_barrel.create_sprites_from_bin_pixel_arrays(['fire_1.bin', 'fire_2.bin', 'fire_3.bin',
                                                               'fire_4.bin'], 23, 54)
        self.fire_barrel.move_all_to(108, 92)
        self.game_over_sprite = cyberpi.sprite()
        self.game_over_sprite.draw_text('GAME 0VER')
        self.game_over_sprite.set_color(250, 10, 10)
        self.game_over_sprite.set_scale(x_size=160, y_size=150)
        self.curtains = cyberpi.sprite()
        self.curtains.draw_pixel(SpriteFactory()._create_curtains_128x128_sprite_array(), 128, 128)
        self.curtains.set_color(*COLORS['screen_green'])
        self.gear = cyberpi.sprite()
        self.gear.draw_pixel('gear')
        self.gear.set_color(*COLORS['console_green'])
        self._set_sprites_visibility()
        gc.collect()

    def _set_sprites_visibility(self):
        self.current_bg.z_min()
        sprites_to_hide = [self.game_over_sprite, self.bg3_grave_top, self.bg3_coffin, self.gear]
        sprites_to_show = [self.current_bg, self.curtains]
        for sprite in sprites_to_hide:
            if sprite is not None:
                sprite.hide()
        for sprite in sprites_to_show:
            if sprite is not None:
                sprite.show()
        # hardcoding background_3 props for now:
        if self.current_bg == self.backgrounds.background_3:
            self.bg3_grave_top.show()
            self.bg3_coffin.show()
        self.curtains.z_max()

    def _start_world(self):
        self._setup_game_sprites()
        self.current_scene = 'world'
        _start_to_render()
        self.curtains.hide()
        if not self._is_initiated:
            self._is_initiated = True
        _safe_play_audio('buzzing')

    def world(self):
        self.current_bg = random.choice([self.backgrounds.background_1, self.backgrounds.background_2,
                                         self.backgrounds.background_3])  # adding for DEBUG
        if not self._is_over:
            self.current_scene = 'world'
            self._set_sprites_visibility()
            _start_to_render()
            self.curtains.hide()

    def show_fire(self):
        if not hasattr(self.fire_barrel, '_last_shown_frame'):
            self.fire_barrel._last_shown_frame = None
        last_frame = self.fire_barrel._last_shown_frame
        frame_numbers = [i for i in range(1, 5) if i != last_frame]
        selected_num = random.choice(frame_numbers)
        if last_frame:
            getattr(self.fire_barrel, 'fire_' + str(last_frame)).hide()
        getattr(self.fire_barrel, 'fire_' + str(selected_num)).show()
        self.fire_barrel._last_shown_frame = selected_num
        sleep(random.uniform(0.06, 0.09))

    def hide_fire(self):
        self.fire_barrel.hide_all()

    def show_idle_dweller_standing(self):
        sprites = self.pip_boy.dweller.skin.standing_sprites
        if len(sprites) >= 2 and sprites[1] is not None:
            sprites[1].hide()
        if len(sprites) >= 2 and sprites[0] is not None:
            sprites[0].show()
        sleep(random.uniform(0.46, 0.49))
        if len(sprites) >= 2 and sprites[0] is not None:
            sprites[0].hide()
        if len(sprites) >= 2 and sprites[1] is not None:
            sprites[1].show()
        sleep(random.uniform(0.46, 0.49))

    def hide_idle_dweller_standing(self):
        for sprite in self.pip_boy.dweller.skin.standing_sprites:
            if sprite is not None:
                sprite.hide()

    def show_idle_dweller_sleeping(self):
        sprites = self.pip_boy.dweller.skin.sleeping_sprites
        if len(sprites) >= 2 and sprites[1] is not None:
            sprites[1].hide()
        if len(sprites) >= 2 and sprites[0] is not None:
            sprites[0].show()
        sleep(random.uniform(0.62, 0.72))
        if len(sprites) >= 2 and sprites[0] is not None:
            sprites[0].hide()
        if len(sprites) >= 2 and sprites[1] is not None:
            sprites[1].show()
        sleep(random.uniform(0.62, 0.72))

    def hide_idle_dweller_sleeping(self):
        for sprite in self.pip_boy.dweller.skin.sleeping_sprites:
            if sprite is not None:
                sprite.hide()

    # Currently handled by the event listener. Leaving to fall back.
    # def adv_pa_toggle_awake(self):
    #     """Toggle between awake and asleep states."""
    #     if not self._is_over:
    #         if self.pip_boy.dweller.is_awake:
    #             self.pip_boy.dweller.is_awake = False
    #         else:
    #             self.pip_boy.dweller.is_awake = True

    def _clean_stage(self):
        self.hide_fire()
        self.hide_idle_dweller_standing()
        self.hide_idle_dweller_sleeping()
        self.current_bg.hide()
        # hardcoding background_3 props for now:
        self.bg3_coffin.hide()
        self.bg3_grave_top.hide()
        self.curtains.show()

    def open_pip_boy(self):
        if not self._is_over:
            self._clean_stage()
            _stop_to_render()
            sleep(0.1)
            self.current_scene = 'pip-boy'
            self.pip_boy.open()

    def close_pip_boy(self):
        self.pip_boy.current_screen = None
        self.current_scene = 'world'
        self.world()

    def game_over(self):
        _stop_to_render()
        sleep(0.1)
        self._is_over = True


try:
    print('Loading...')
    cyberpi.audio.set_vol(VOLUME)
    cyberpi.background.fill(*COLORS['screen_green'])
    cyberpi.display.set_brush(*COLORS['console_green'])
    cyberpi.console.println('Collecting garbage...')
    gc.collect()
    sleep(2)
    gc.enable()
    cyberpi.console.clear()
    cyberpi.console.print('Loading...')
    preload_bin_arrays()
    game = FO2GameWorld()
    game._start_world()
except Exception as err:
    try:
        _stop_to_render()
        cyberpi.console.print('ERROR: ' + str(err))
    except Exception:
        print('ERROR: ' + str(err))


# ---------------------------------------------------------
# Event handlers
# ---------------------------------------------------------
@cyberpi.event.start
def main_game_loop():
    if DEBUG:
        print('STARTED: Main loop handler')
    global game
    gc_counter = 0
    while True:
        if game and game._is_initiated:
            if not game.pip_boy.dweller._is_changing_skin:
                if game.pip_boy.current_screen == 'wait':  # temporarily
                    game.pip_boy.display_change_skin_menu()  # temporarily
                cyberpi.broadcast('play')
            else:
                cyberpi.broadcast('display_pip_boy_wait')  # temporarily
            gc_counter += 1
            if gc_counter >= 200:
                gc.collect()
                gc_counter = 0
        else:
            # _show_botton_left_label(text='No game instance\n' + str(cyberpi.timer.get()), position='center')
            pass
        sleep(0.05)


@cyberpi.event.receive('display_pip_boy_wait')
def display_pip_boy_wait():
    if game.pip_boy.current_screen != 'wait':
        game.pip_boy.display_wait()  # temporarily


# @cyberpi.event.start
@cyberpi.event.receive('play')
def looped_animations_dweller():
    # if DEBUG:
    #     print('STARTED: Vault Dweller animation handler')
    global game
    # while True:
    if game:
        if game._is_initiated and not game._is_over and game.current_scene == 'world':
            game.pip_boy.dweller.set_skin_direction()
            if game.pip_boy.dweller.is_awake:
                game.hide_idle_dweller_sleeping()
                game.show_idle_dweller_standing()
            else:
                game.hide_idle_dweller_standing()
                game.show_idle_dweller_sleeping()
    sleep(0.01)


# @cyberpi.event.start
@cyberpi.event.receive('play')
def looped_animation_fire():
    # if DEBUG:
    #     print('STARTED: Fire animation handler')
    global game
    # while True:
    if game:
        if game._is_initiated and not game._is_over and game.current_scene == 'world':
            game.show_fire()
    sleep(0.01)


# @cyberpi.event.start
@cyberpi.event.receive('play')
def looped_animation_game_over_gc():
    # if DEBUG:
    #     print('STARTED: Game Over animation handler')
    global game
    # while True:
    if game:
        if game._is_initiated and game._is_over:
            game._clean_stage()
            game.curtains.show()
            game.curtains.z_max()
            game.game_over_sprite.show()
            game.game_over_sprite.z_max()
            _render_me()
    sleep(0.5)


@cyberpi.event.is_press('a')
def on_press_a():
    global game
    if game:
        if not game._is_over:
            if game.current_scene == 'world':
                if DEBUG:
                    game.game_over()
            elif game.current_scene == 'pip-boy':
                _safe_play_audio('click')
                if game.pip_boy.current_screen == 'main':
                    game.close_pip_boy()
                elif game.pip_boy.current_screen == 'stats':
                    game.pip_boy.display_main()
                elif game.pip_boy.current_screen == 'change_skin_menu' and not game.pip_boy.dweller._is_changing_skin:
                    game.pip_boy.display_stats()
                else:
                    pass  # Placeholder for future functionality
        else:
            if DEBUG:
                game._is_over = False
                sleep(0.5)  # Wait to settle animations
                game.world()
            pass
    sleep(0.01)


@cyberpi.event.is_press('b')
def on_press_b():
    global game
    if game:
        if game.current_scene == 'world':
            # for DEBUG, not mem safe
            if not game.pip_boy.dweller._is_changing_skin:
                # game.adv_pa_toggle_awake()
                cyberpi.broadcast('toggle_awake')  # trying if broadcaster available with constant 'play' broadcasting
        elif game.current_scene == 'pip-boy':
            _safe_play_audio('click')
            if game.pip_boy.current_screen == 'main':
                game.pip_boy.display_stats()
            elif game.pip_boy.current_screen == 'stats':
                game.pip_boy.display_change_skin_menu()
            elif game.pip_boy.current_screen == 'change_skin_menu':
                if not game.pip_boy.dweller._is_changing_skin:
                    if game.pip_boy.dweller.current_skin_type == 'vault_suit':
                        game.pip_boy.dweller.change_skin('adv_power_armor')
                    else:
                        game.pip_boy.dweller.change_skin('vault_suit')
                else:
                    pass
            else:
                pass  # Placeholder for future functionality
        else:
            pass  # Placeholder for future functionality
    sleep(0.01)


@cyberpi.event.receive('toggle_awake')
def adv_pa_toggle_awake():
    """Toggle between awake and asleep states."""
    global game
    if not game._is_over:
        if game.pip_boy.dweller.is_awake:
            game.pip_boy.dweller.is_awake = False
        else:
            game.pip_boy.dweller.is_awake = True
    sleep(0.01)


@cyberpi.event.is_press('middle')
def on_press_middle():
    global game
    _safe_play_audio('click')
    if game:
        if game.current_scene != 'pip-boy':
            game.open_pip_boy()
        else:
            if not game.pip_boy.dweller._is_changing_skin:
                game.close_pip_boy()
    sleep(0.01)


@cyberpi.event.is_press('up')
def on_press_up():
    global game
    if game:
        if game.current_scene == 'world':
            game.pip_boy.dweller.y_direction = 'north'
        elif game.current_scene == 'pip-boy':
            _safe_play_audio('click')
            pass  # Placeholder for future functionality
    sleep(0.01)


@cyberpi.event.is_press('down')
def on_press_down():
    global game
    if game:
        if game.current_scene == 'world':
            game.pip_boy.dweller.y_direction = 'south'
        elif game.current_scene == 'pip-boy':
            _safe_play_audio('click')
            pass  # Placeholder for future functionality
    sleep(0.01)


@cyberpi.event.is_press('left')
def on_press_left():
    global game
    if game:
        if game.current_scene == 'world':
            game.pip_boy.dweller.x_direction = 'west'
        elif game.current_scene == 'pip-boy':
            _safe_play_audio('click')
            pass  # Placeholder for future functionality
    sleep(0.01)


@cyberpi.event.is_press('right')
def on_press_right():
    global game
    if game:
        if game.current_scene == 'world':
            game.pip_boy.dweller.x_direction = 'east'
        elif game.current_scene == 'pip-boy':
            _safe_play_audio('click')
            pass  # Placeholder for future functionality
    sleep(0.01)
