from panda3d.core import Point3
from direct.showbase import Audio3DManager
import os
import random

class SFX:
    def __init__(self, base):
        self.base = base
        self.sounds = {}
        # Initialize Audio3DManager with the first sfxManager and the camera
        self.audio3d = Audio3DManager.Audio3DManager(base.sfxManagerList[0], base.camera)

    def load_sound(self, sound_name, sound_file):
        """Load a sound effect from a file."""
        if sound_name not in self.sounds:
            sound_path = os.path.join("sounds", sound_file)  # Assuming sounds are in a folder named "sounds"
            if not os.path.exists(sound_path):
                print(f"Warning: Sound file '{sound_file}' does not exist!")
                return None
            # Load the sound using Audio3DManager's loadSfx method
            sound = self.audio3d.loadSfx(sound_path)
            self.sounds[sound_name] = sound
            print(f"Sound '{sound_name}' loaded successfully.")
        return self.sounds.get(sound_name)

    def play_sound(self, sound_name, position=Point3(0, 0, 0), loop=False, volume=1.0, play_rate=1.0, balance=0.0, max_dist=10.0, min_dist=0.1):
        """Play the sound at a specific position in 3D space with added options for variation."""
        sound = self.sounds.get(sound_name)
        if not sound:
            print(f"Error: Sound '{sound_name}' not loaded.")
            return

        # Set various properties for the sound
        sound.set_volume(volume)
        sound.set_balance(balance)  # Balance the sound between left and right
        sound.set_loop(loop)  # Loop the sound
        sound.set_loop_count(0 if loop else 1)  # Loop indefinitely if requested
        sound.set3dMaxDistance(max_dist)  # Set maximum distance for sound falloff
        sound.set3dMinDistance(min_dist)  # Set minimum distance for sound falloff

        # Set the sound's 3D position and velocity
        sound.set3dAttributes(position.get_x(), position.get_y(), position.get_z(), 0, 0, 0)  # You can modify the velocity as needed

        # Add subtle play rate variation to the sound when the bottle breaks (randomization)
        sound.setPlayRate(play_rate * random.uniform(0.8, 1.2))  # Variation from 90% to 110% of the original play rate

        # Attach the sound to the camera (or another object, if desired)
        self.audio3d.attachSoundToObject(sound, self.base.camera)
        
        # Play the sound
        sound.play()
        print(f"Playing sound '{sound_name}' at position {position}.")

    def stop_sound(self, sound_name):
        """Stop a specific sound by name."""
        sound = self.sounds.get(sound_name)
        if sound:
            sound.stop()
            print(f"Stopped sound '{sound_name}'.")

    def stop_all_sounds(self):
        """Stop all sounds."""
        for sound in self.sounds.values():
            sound.stop()
        print("Stopped all sounds.")

# Example usage:
# sfx = SFX(base)  # Assuming base is the main Panda3D instance
# sfx.load_sound("bottle_break", "break.wav")
# sfx.play_sound("bottle_break", position=Point3(10, 0, 0), volume=0.8, play_rate=1.0)
