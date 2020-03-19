import sys
import pygame
import random
import math


class Camera:
    def __init__(self, bubble_radius, bubbles_in_row, number_of_rows, num_rows_before_gun):
        self.win_w = 2*bubble_radius*bubbles_in_row
        self.win_h = 2*bubble_radius*20
        self.screen = pygame.display.set_mode([self.win_w, self.win_h])
        self.pos_y = int((number_of_rows+num_rows_before_gun)*2*bubble_radius) - self.win_h + bubble_radius
        self.start_y = self.pos_y

    def from_world_to_screen(self, world_x, world_y):
        screen_x = int(world_x)
        screen_y = int(world_y - self.pos_y)
        return [screen_x, screen_y]

    def from_screen_to_world(self, screen_x, screen_y):
        world_x = screen_x
        world_y = screen_y + self.pos_y
        return [world_x, world_y]

    def update(self):
        self.screen.fill((0, 0, 0))
        if pygame.key.get_pressed()[pygame.K_UP]:
            self.pos_y -= 2
        elif pygame.key.get_pressed()[pygame.K_DOWN]:
            self.pos_y += 2


class Bubble:
    def __init__(self, row, col, x, y, radius, bubble_type, debug_text):
        self.row = row
        self.col = col
        self.x = x
        self.y = y
        self.r = radius
        self.type = bubble_type

        self.text = None
        self.textRect = None
        if debug_text:
            self.text = debug_text
            self.textRect = self.text.get_rect()

    def render(self, camera, bubble_colors, highlighted=False):
        if self.type < 0:
            return
        screen_pos = camera.from_world_to_screen(self.x, self.y)
        radius = int(self.r)
        pygame.draw.circle(camera.screen, bubble_colors[self.type], screen_pos, radius, 0)
        if highlighted:
            pygame.draw.circle(camera.screen, (255, 255, 255), screen_pos, radius+2, 2)

        if self.text:
            self.textRect.center = screen_pos
            camera.screen.blit(self.text, self.textRect)


class Cannon:
    def __init__(self, camera, bubble_radius, number_of_rows, num_rows_before_gun):
        self.x = int(camera.win_w / 2)
        self.y = int((number_of_rows + num_rows_before_gun) * 2 * bubble_radius)
        self.r = bubble_radius
        self.current_bubble_type = 0
        self.trace_points = []

    def render(self, camera, bubble_colors):
        screen_pos = camera.from_world_to_screen(self.x, self.y)
        pygame.draw.circle(camera.screen, bubble_colors[self.current_bubble_type], screen_pos, self.r, 0)
        pygame.draw.circle(camera.screen, (255, 255, 255), screen_pos, self.r, 1)

        for i, p in enumerate(self.trace_points):
            if i == 0:
                continue
            p1 = camera.from_world_to_screen(self.trace_points[i - 1][0], self.trace_points[i - 1][1])
            p2 = camera.from_world_to_screen(self.trace_points[i][0], self.trace_points[i][1])
            pygame.draw.line(camera.screen, (255, 255, 255), p1, p2, 1)

            if i == len(self.trace_points) - 1:
                pygame.draw.circle(camera.screen, (255, 255, 255), p2, self.r, 1)

    def update(self, mouse_world, game_field):
        if pygame.key.get_pressed()[pygame.K_1]:
            self.current_bubble_type = 0
        elif pygame.key.get_pressed()[pygame.K_2]:
            self.current_bubble_type = 1
        elif pygame.key.get_pressed()[pygame.K_3]:
            self.current_bubble_type = 2
        elif pygame.key.get_pressed()[pygame.K_4]:
            self.current_bubble_type = 3
        elif pygame.key.get_pressed()[pygame.K_5]:
            self.current_bubble_type = 4
        elif pygame.key.get_pressed()[pygame.K_6]:
            self.current_bubble_type = 5
        elif pygame.key.get_pressed()[pygame.K_7]:
            self.current_bubble_type = 6
        elif pygame.key.get_pressed()[pygame.K_8]:
            self.current_bubble_type = 7

        if game_field.flying_bubble is None:
            vec = [mouse_world[0] - self.x, mouse_world[1] - self.y]
            vec_len = math.sqrt(vec[0] * vec[0] + vec[1] * vec[1])
            direction = [vec[0] / vec_len, vec[1] / vec_len]
            wx = self.x
            wy = self.y
            flying_speed = 10
            collision = None
            points = [[self.x, self.y]]
            while collision is None:
                tmp_x = wx + direction[0]*flying_speed
                tmp_y = wy + direction[1]*flying_speed

                if tmp_x - self.r <= 0:
                    tmp_x = self.r
                    direction[0] *= -1
                    points.append([tmp_x, tmp_y])
                elif tmp_x + self.r >= 330:
                    tmp_x = 330 - self.r
                    direction[0] *= -1
                    points.append([tmp_x, tmp_y])

                collision = game_field.check_collision(tmp_x, tmp_y, self.r)
                if collision:
                    new_pos = game_field.find_place_to_add_flying_bubble(collision, tmp_x, tmp_y)
                    wp = game_field.get_bubble_world_position(new_pos[0], new_pos[1])
                    points.append(wp)
                else:
                    wx = tmp_x
                    wy = tmp_y
            self.trace_points = points

    def fire(self, mouse_world, game_field):
        if game_field.flying_bubble is not None:
            return
        vec = [mouse_world[0] - self.x, mouse_world[1] - self.y]
        vec_len = math.sqrt(vec[0]*vec[0] + vec[1]*vec[1])
        direction = [vec[0]/vec_len, vec[1]/vec_len]
        game_field.flying_bubble = Bubble(-1, -1, self.x, self.y, self.r, self.current_bubble_type, None)
        game_field.flying_bubble_direction = direction
        self.current_bubble_type = random.randint(0, game_field.number_of_colors - 1)


class GameField:
    def __init__(self, number_of_rows, bubbles_in_row, bubble_radius, number_of_colors, font_obj):
        self.colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 128, 128),
                       (128, 0, 128), (255, 0, 255), (0, 128, 0)]
        self.number_of_colors = number_of_colors
        self.r = bubble_radius
        self.top_pos = 0
        self.bubbles = []
        self.highlightedBubbles = []
        self.flying_bubble = None
        self.flying_bubble_direction = [0, 0]
        self.deleting_bubbles = []
        self.falling_bubbles = []

        color_index = 0
        for row in range(number_of_rows):
            bubbles_row = []
            for col in range(bubbles_in_row):
                bubble_color = random.randint(0, number_of_colors-1)  # color_index
                if row == 0:
                    bubble_color = -1
                bubble_pos = self.get_bubble_world_position(row, col)
                debug_text = font_obj.render(str(row) + "," + str(col), True, (255, 255, 255), (0, 0, 0))
                bubble = Bubble(row, col, bubble_pos[0], bubble_pos[1], bubble_radius, bubble_color, debug_text=None)
                bubbles_row.append(bubble)

                color_index += 1
                if color_index == number_of_colors:
                    color_index = 0

                if row % 2 != 0 and col == 9:
                    break
            self.bubbles.append(bubbles_row)

    def get_bubble_world_position(self, row, col):
        world_x = self.r + 2*self.r*col
        world_y = self.r + 2*self.r*row
        if row % 2 != 0:
            world_x = 2*self.r + 2*self.r*col
            world_y = self.r + 2*self.r*row
        return [world_x, world_y + self.top_pos]

    def render(self, camera, cannon):
        bottom_bubble_pos_y = 0
        for bubbles_row in self.bubbles:
            for bubble in bubbles_row:
                if bubble is not None:
                    highlighted = False
                    if bubble in self.highlightedBubbles:
                        highlighted = True
                    bubble.render(camera, self.colors, highlighted)
                    if bubble.y > bottom_bubble_pos_y:
                        bottom_bubble_pos_y = bubble.y

        if cannon.y - bottom_bubble_pos_y > 7*self.r*2 and self.bubbles[0][0].y < camera.start_y:
            self.move_field(1)

        pygame.draw.rect(camera.screen, (255, 0, 0), (0, -2 - camera.pos_y + 2*self.r, camera.win_w, 2))
        pygame.draw.rect(camera.screen, (128, 128, 128), (0, self.top_pos - 2 - camera.pos_y + 2*self.r, camera.win_w, 2))

        if self.flying_bubble is not None:
            self.flying_bubble.render(camera, self.colors, False)

        for bubble in self.deleting_bubbles:
            bubble.render(camera, self.colors, False)

        for bubble in self.falling_bubbles:
            bubble.render(camera, self.colors, False)

    def update(self, camera):
        # if pygame.key.get_pressed()[pygame.K_w]:
        #     self.move_field(-1)
        # elif pygame.key.get_pressed()[pygame.K_s]:
        #     self.move_field(1)

        for bubble in self.deleting_bubbles:
            bubble.r -= 1
            if bubble.r <= 0:
                self.deleting_bubbles.remove(bubble)

        for bubble in self.falling_bubbles:
            bubble.y += 5
            if bubble.y >= camera.pos_y + camera.win_h + bubble.r*2:
                self.falling_bubbles.remove(bubble)

        if self.flying_bubble is not None:
            flying_speed = 10
            tmp_x = self.flying_bubble.x + self.flying_bubble_direction[0]*flying_speed
            tmp_y = self.flying_bubble.y + self.flying_bubble_direction[1]*flying_speed

            if tmp_x - self.r <= 0:
                tmp_x = self.r
                self.flying_bubble_direction[0] *= -1
            elif tmp_x + self.r >= 330:
                tmp_x = 330 - self.r
                self.flying_bubble_direction[0] *= -1

            collision = self.check_collision(tmp_x, tmp_y, self.r)
            if collision:
                new_pos = self.find_place_to_add_flying_bubble(collision, tmp_x, tmp_y)
                wp = self.get_bubble_world_position(new_pos[0], new_pos[1])
                if new_pos[0] >= len(self.bubbles):
                    self.add_empty_row()
                self.flying_bubble.row = new_pos[0]
                self.flying_bubble.col = new_pos[1]
                self.flying_bubble.x = wp[0]
                self.flying_bubble.y = wp[1]
                self.bubbles[self.flying_bubble.row][self.flying_bubble.col] = self.flying_bubble
                group = []
                self.find_group_recursion(self.flying_bubble, self.flying_bubble.type, group)
                if len(group) >= 3:
                    # delete group of bubbles with same color
                    for bubble in group:
                        self.bubbles[bubble.row][bubble.col] = None
                        self.deleting_bubbles.append(bubble)
                    # find and delete hanging groups of bubbles
                    # all bubbles' groups must have connections with top row
                    connected_bubbles = []
                    for bubble in self.bubbles[0]:
                        if bubble is not None:
                            self.find_group_recursion(bubble, "any", connected_bubbles)
                    for bubbles_row in self.bubbles:
                        for bubble in bubbles_row:
                            if bubble is None:
                                continue
                            if bubble not in connected_bubbles:
                                self.bubbles[bubble.row][bubble.col] = None
                                self.falling_bubbles.append(bubble)
                self.flying_bubble = None
            else:
                self.flying_bubble.x = tmp_x
                self.flying_bubble.y = tmp_y

    def move_field(self, direction):
        speed = 2
        self.top_pos += direction * speed
        if self.top_pos < 0:
            self.top_pos = 0
            return
        for bubbles_row in self.bubbles:
            for bubble in bubbles_row:
                if bubble is not None:
                    bubble.y += direction * speed

    def check_collision(self, x, y, r):
        for bubbles_row in reversed(self.bubbles):
            for bubble in bubbles_row:
                if bubble is not None:
                    square_distance = (x - bubble.x)*(x - bubble.x) + (y - bubble.y)*(y - bubble.y)
                    if square_distance <= (bubble.r + r) *(bubble.r + r):
                        return bubble
        return None

    def get_bubble_at(self, row, col):
        if row >= len(self.bubbles) or row < 0:
            return None
        if col >= len(self.bubbles[row]) or col < 0:
            return None
        return self.bubbles[row][col]

    @staticmethod
    def get_neighborhood_indexes(row, col):
        indx = [[row, col-1], [row, col+1], [row-1, col], [row+1, col]]
        if row % 2 == 0:
            indx.append([row-1, col-1])
            indx.append([row+1, col-1])
        else:
            indx.append([row-1, col+1])
            indx.append([row+1, col+1])
        return indx

    def get_neighborhood(self, row, col):
        neighborhood = []
        indx = GameField.get_neighborhood_indexes(row, col)
        for i in indx:
            bubble = self.get_bubble_at(i[0], i[1])
            if bubble is not None:
                neighborhood.append(bubble)
        return neighborhood

    def find_group_recursion(self, bubble, bubble_type, group):
        if bubble_type != "any":
            if bubble.type != bubble_type:
                return
        if bubble not in group:
            group.append(bubble)
            neighborhood = self.get_neighborhood(bubble.row, bubble.col)
            for n in neighborhood:
                if n in group:
                    continue
                self.find_group_recursion(n, bubble_type, group)

    def add_empty_row(self):

        next_row_index = len(self.bubbles)
        num_bubbles_in_row = len(self.bubbles[0])
        if next_row_index % 2 == 0:
            row = [None]*num_bubbles_in_row
        else:
            row = [None]*(num_bubbles_in_row - 1)
        self.bubbles.append(row)

    def find_place_to_add_flying_bubble(self, collision, flying_bubble_x, flying_bubble_y):
        ni = GameField.get_neighborhood_indexes(collision.row, collision.col)
        min_dist = 10000
        new_pos = []
        for i in ni:
            if self.get_bubble_at(i[0], i[1]) is not None:
                continue
            wp = self.get_bubble_world_position(i[0], i[1])
            vec = [wp[0] - flying_bubble_x, wp[1] - flying_bubble_y]
            vec_len = math.sqrt(vec[0]*vec[0] + vec[1]*vec[1])
            if vec_len < min_dist:
                min_dist = vec_len
                new_pos = [i[0], i[1]]
        return new_pos


class Settings:
    def __init__(self):
        self.bubble_radius = 15
        self.bubbles_in_row = 11
        self.number_of_rows = 20
        self.num_rows_before_gun = 6


pygame.init()
_clock = pygame.time.Clock()
_font = pygame.font.SysFont('Arial', 10)

_settings = Settings()
_camera = Camera(_settings.bubble_radius, _settings.bubbles_in_row,
                 _settings.number_of_rows, _settings.num_rows_before_gun)
_game_field = GameField(_settings.number_of_rows, _settings.bubbles_in_row, _settings.bubble_radius, 3, _font)
_cannon = Cannon(_camera, _settings.bubble_radius, _settings.number_of_rows, _settings.num_rows_before_gun)


def debug_highlight_bubble_under_mouse_and_neighborhood(mouse, game_field):
    bubble = game_field.check_collision(mouse[0], mouse[1], 0)
    if bubble is not None:
        game_field.highlightedBubbles = game_field.get_neighborhood(bubble.row, bubble.col) + [bubble]
    else:
        game_field.highlightedBubbles = []


def debug_highlight_bubble_under_mouse_group(mouse, game_field):
    bubble = game_field.check_collision(mouse[0], mouse[1], 0)
    if bubble is not None:
        group = []
        game_field.find_group_recursion(bubble, bubble.type, group)
        game_field.highlightedBubbles = group
    else:
        game_field.highlightedBubbles = []


while True:

    mouse_screen = pygame.mouse.get_pos()
    mouse_world = _camera.from_screen_to_world(mouse_screen[0], mouse_screen[1])
    # debug_highlight_bubble_under_mouse_and_neighborhood(mouse_world, _game_field)
    # debug_highlight_bubble_under_mouse_group(mouse_world, _game_field)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pass
        elif event.type == pygame.MOUSEBUTTONUP:
            _cannon.fire(mouse_world, _game_field)

    # pygame.display.set_caption(str(mouse_world))

    _camera.update()
    _cannon.update(mouse_world, _game_field)
    _game_field.update(_camera)

    _game_field.render(_camera, _cannon)
    _cannon.render(_camera, _game_field.colors)

    pygame.display.flip()
    _clock.tick(60)
