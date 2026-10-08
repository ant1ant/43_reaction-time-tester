import pygame
import math
import array
from .round import Round


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (90, 90, 90)
GREEN = (40, 180, 90)
BLUE = (50, 90, 170)
RED = (180, 50, 50)
DARK_BLUE = (30, 50, 100)


class GameEngine:

    def __init__(self, width, height, rounds_total=5,
                 min_wait_ms=1000, max_wait_ms=3000):

        self.width = width
        self.height = height

        self.rounds_total = rounds_total
        self.min_wait_ms = min_wait_ms
        self.max_wait_ms = max_wait_ms

        self.round = Round(self.min_wait_ms, self.max_wait_ms)
        self.reaction_times = []

        self.result_shown_at = None
        self.result_pause_ms = 1000

        self.font = pygame.font.SysFont("Arial", 30)
        self.big_font = pygame.font.SysFont("Arial", 46)
        self.small_font = pygame.font.SysFont("Arial", 24)

        self.game_over = False
        self.difficulty_menu = False

        self.false_start = False

        self.sounds = {}
        self._create_sounds()

    # --------------------------------------------------
    # SOUND
    # --------------------------------------------------

    def _create_tone(self, frequency, duration_ms, volume=0.4):
        sample_rate = 44100
        sample_count = int(sample_rate * duration_ms / 1000)

        samples = array.array("h")

        for i in range(sample_count):
            value = int(
                32767
                * volume
                * math.sin(2 * math.pi * frequency * i / sample_rate)
            )
            samples.append(value)

        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _create_sounds(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            self.sounds["go"] = self._create_tone(900, 180, 0.4)
            self.sounds["false_start"] = self._create_tone(250, 350, 0.4)
            self.sounds["end"] = self._create_tone(500, 200, 0.4)

        except pygame.error:
            self.sounds = {}

    def _play_sound(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    # --------------------------------------------------
    # INPUT
    # --------------------------------------------------

    def handle_event(self, event):

        # Results/difficulty screen
        if self.game_over:

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_1:
                    self._start_game(
                        rounds_total=5,
                        min_wait_ms=1500,
                        max_wait_ms=3000
                    )

                elif event.key == pygame.K_2:
                    self._start_game(
                        rounds_total=5,
                        min_wait_ms=1000,
                        max_wait_ms=2500
                    )

                elif event.key == pygame.K_3:
                    self._start_game(
                        rounds_total=7,
                        min_wait_ms=500,
                        max_wait_ms=1500
                    )

                elif event.key == pygame.K_ESCAPE:
                    self.difficulty_menu = False

            return

        is_click = event.type == pygame.MOUSEBUTTONDOWN
        is_space = (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_SPACE
        )

        if is_click or is_space:

            result = self.round.register_input()

            # False start
            if self.round.state == "false_start":
                self.false_start = True
                self.result_shown_at = pygame.time.get_ticks()
                self._play_sound("false_start")
                return

            # Valid reaction
            if result is not None:
                self.reaction_times.append(result)
                self.result_shown_at = pygame.time.get_ticks()

    def handle_input(self):
        pass

    # --------------------------------------------------
    # GAME UPDATE
    # --------------------------------------------------

    def update(self):

        if self.game_over:
            return

        previous_state = self.round.state

        self.round.update()

        # Play go sound when waiting changes to go
        if previous_state == "waiting" and self.round.state == "go":
            self._play_sound("go")

        # Handle result or false start pause
        if self.round.state in ("result", "false_start"):

            now = pygame.time.get_ticks()

            if (
                self.result_shown_at is not None
                and now - self.result_shown_at >= self.result_pause_ms
            ):
                self._start_next_round()

    # --------------------------------------------------
    # ROUND MANAGEMENT
    # --------------------------------------------------

    def _start_next_round(self):

        # If all rounds are complete
        if len(self.reaction_times) >= self.rounds_total:
            self.game_over = True
            self.difficulty_menu = True
            self._play_sound("end")
            return

        self.false_start = False
        self.result_shown_at = None

        self.round = Round(
            self.min_wait_ms,
            self.max_wait_ms
        )

    def _start_game(self, rounds_total, min_wait_ms, max_wait_ms):

        self.rounds_total = rounds_total
        self.min_wait_ms = min_wait_ms
        self.max_wait_ms = max_wait_ms

        self.reaction_times = []

        self.game_over = False
        self.difficulty_menu = False
        self.false_start = False

        self.result_shown_at = None

        self.round = Round(
            self.min_wait_ms,
            self.max_wait_ms
        )

    # --------------------------------------------------
    # AVERAGE
    # --------------------------------------------------

    def average_reaction_ms(self):

        if not self.reaction_times:
            return 0

        return round(
            sum(self.reaction_times)
            / len(self.reaction_times)
        )

    # --------------------------------------------------
    # TEXT HELPER
    # --------------------------------------------------

    def draw_text(self, screen, text, font, y, color=WHITE):

        text_surface = font.render(
            text,
            True,
            color
        )

        text_rect = text_surface.get_rect(
            center=(self.width // 2, y)
        )

        screen.blit(
            text_surface,
            text_rect
        )

    # --------------------------------------------------
    # NORMAL GAME SCREEN
    # --------------------------------------------------

    def render_game(self, screen):

        if self.round.state == "waiting":

            bg = GRAY
            message = "Wait for green..."

        elif self.round.state == "go":

            bg = GREEN
            message = "CLICK NOW!"

        elif self.round.state == "result":

            bg = BLUE
            message = f"{self.round.reaction_ms} ms"

        elif self.round.state == "false_start":

            bg = RED
            message = "FALSE START!"

        else:

            bg = GRAY
            message = "Wait..."

        screen.fill(bg)

        text_surf = self.big_font.render(
            message,
            True,
            WHITE
        )

        text_rect = text_surf.get_rect(
            center=(self.width // 2, self.height // 2)
        )

        screen.blit(
            text_surf,
            text_rect
        )

        # Round number
        round_num = min(
            len(self.reaction_times) + 1,
            self.rounds_total
        )

        round_text = self.font.render(
            f"Round {round_num}/{self.rounds_total}",
            True,
            WHITE
        )

        screen.blit(
            round_text,
            (10, 10)
        )

        # Average
        avg_text = self.font.render(
            f"Avg: {self.average_reaction_ms()} ms",
            True,
            WHITE
        )

        screen.blit(
            avg_text,
            (self.width - 190, 10)
        )

    # --------------------------------------------------
    # RESULTS SCREEN
    # --------------------------------------------------

    def render_results(self, screen):

        screen.fill(DARK_BLUE)

        self.draw_text(
            screen,
            "GAME OVER!",
            self.big_font,
            55
        )

        self.draw_text(
            screen,
            "Final Results",
            self.font,
            105
        )

        y = 150

        for i, reaction in enumerate(self.reaction_times):

            text = f"Round {i + 1}: {reaction} ms"

            self.draw_text(
                screen,
                text,
                self.small_font,
                y
            )

            y += 30

        average_text = f"Average: {self.average_reaction_ms()} ms"

        self.draw_text(
            screen,
            average_text,
            self.font,
            300
        )

        self.draw_text(
            screen,
            "Choose difficulty",
            self.font,
            345
        )

        self.draw_text(
            screen,
            "1 - Easy     2 - Medium     3 - Hard",
            self.small_font,
            380
        )

        self.draw_text(
            screen,
            "Press ESC to stay on this screen",
            self.small_font,
            410
        )

    # --------------------------------------------------
    # MAIN RENDER
    # --------------------------------------------------

    def render(self, screen):

        if self.game_over:
            self.render_results(screen)
        else:
            self.render_game(screen)
