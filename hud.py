from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

class HUD:
    def __init__(self, game, bottle_manager):
        self.game = game
        self.bottle_manager = bottle_manager
        self.ammo = 100
        self.bottles_total = self.bottle_manager.get_total_bottles()
        self.bottles_shot = 0
        self.timer = 6000  # Reset scene timer (seconds)
        
        # Create HUD elements
        self.ammo_text = self.create_text("Ammo: 100", (-1.3, 0.85))
        self.bottle_text = self.create_text(f"Bottles: 0/{self.bottles_total}", (-1.3, 0.75))
        self.timer_text = self.create_text(f"Time Left: {self.timer}s", (-1.3, 0.65))
        
        # Start the countdown task
        self.game.taskMgr.add(self.update_timer, "update_timer")
    
    def create_text(self, text, pos):
        return OnscreenText(text=text, pos=pos, scale=0.07, fg=(1, 1, 1, 1), align=TextNode.ALeft, mayChange=True)
    
    def update_ammo(self, amount):
        self.ammo = max(0, self.ammo + amount)  # Prevent negative ammo
        self.ammo_text.setText(f"Ammo: {self.ammo}")
    
    def update_bottles(self):
        self.bottles_shot += 1
        self.bottle_text.setText(f"Bottles: {self.bottles_shot}/{self.bottles_total}")
    def update_bottles_total(self, total):
        self.bottles_total += total
        self.bottle_text.setText(f"Bottles: {self.bottles_shot}/{self.bottles_total}")
    def update_timer(self, task):
        if self.timer > 0:
            self.timer -= 1
            self.timer_text.setText(f"Time Left: {self.timer}s")
            return task.again  # Repeat every second
        else:
            self.game.reset_scene()
            return task.done  # Stop when timer reaches zero
        
    def reset(self):
        self.ammo = 100
        self.bottles_shot = 0
        
        self.timer = 6000
        
        # Update text elements
        self.ammo_text.setText("Ammo: 100")
        self.bottle_text.setText(f"Bottles: 0/{self.bottles_total}")
        self.timer_text.setText(f"Time Left: {self.timer}s")

        # Restart the countdown task
        self.game.taskMgr.remove("update_timer")
        self.game.taskMgr.add(self.update_timer, "update_timer")
