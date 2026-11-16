import glob
import os

# Custom aesthetic vibrant palette for Language Donut Graph in 3D Contrib:
# JavaScript -> Electric Cyber Gold
# TypeScript -> Vibrant Neon Cyan
# HTML       -> Hot Cyber Fuchsia
# Python     -> Electric Neon Violet
# other      -> Sleek Neon Indigo
COLOR_MAP = {
    '#f1e05a': '#FFE600',
    '#3178c6': '#00F0FF',
    '#e34c26': '#FF007F',
    '#3572a5': '#A855F7',
    '#3572A5': '#A855F7',
    '#444444': '#6366F1',
}

def main():
    pattern = os.path.join('profile-3d-contrib', '*.svg')
    files = glob.glob(pattern)
    if not files:
        # Fallback if run from a different root
        pattern = os.path.join(os.path.dirname(__file__), '..', 'profile-3d-contrib', '*.svg')
        files = glob.glob(pattern)

    print(f"Scanning {len(files)} 3D profile SVG files...")
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        updated = content
        for old_color, new_color in COLOR_MAP.items():
            updated = updated.replace(old_color, new_color)

        if updated != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated)
            print(f"Successfully applied aesthetic colors to {os.path.basename(file_path)}")

if __name__ == '__main__':
    main()
