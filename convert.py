import os
import subprocess

def convert_blend_to_bam(blend_file, output_dir):
    """Convert a single .blend file to .bam using blend2bam."""
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Construct the output .bam file path
    bam_file = os.path.join(output_dir, os.path.splitext(os.path.basename(blend_file))[0] + '.bam')
    
    # Run the blend2bam command with the --textures copy option
    subprocess.run(['blend2bam', '--textures', 'copy', blend_file, bam_file], check=True)
    print(f"Converted {blend_file} to {bam_file}")

def process_directory(root_dir):
    """Process all .blend files in the directory and subdirectories."""
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith('.blend'):
                blend_file = os.path.join(dirpath, filename)
                # Calculate the relative path of the blend file
                rel_path = os.path.relpath(blend_file, root_dir)
                # Replace the .blend extension with .bam
                bam_rel_path = os.path.splitext(rel_path)[0] + '.bam'
                # Determine the output directory
                output_dir = os.path.join(root_dir, os.path.dirname(bam_rel_path))
                # Convert the blend file to bam
                convert_blend_to_bam(blend_file, output_dir)

if __name__ == "__main__":
    project_dir = os.getcwd()  # Get the current working directory
    process_directory(project_dir)
