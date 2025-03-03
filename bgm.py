
from panda3d.core import AudioManager
from panda3d.core import AudioSound
from panda3d.core import NodePath
from panda3d.core import Filename
class BGMPlayer:
    def __init__(self, audio_file):
        # Correct the line to load the sound
        self.bgm_sound = base.loader.loadSfx(audio_file)

        # Optionally, play the sound if you want it to start immediately
        

        if not self.bgm_sound:
            print(f"Error: Unable to load {audio_file}")
            return
        
        # Set the background music to loop
        self.bgm_sound.set_loop(True)
        
        # Set the volume to a reasonable level (you can adjust this)
        self.bgm_sound.set_volume(0.5)
        self.bgm_sound.play()
        
    def play_bgm(self):
        # Play the background music
        self.bgm_sound.play()
        print("Background music is now playing.")
        
    def stop_bgm(self):
        # Stop the background music
        self.bgm_sound.stop()
        print("Background music stopped.")
        
    def pause_bgm(self):
        # Pause the background music
        self.bgm_sound.pause()
        print("Background music paused.")
    
    def resume_bgm(self):
        # Resume playing the background music if paused
        self.bgm_sound.play()
        print("Background music resumed.")