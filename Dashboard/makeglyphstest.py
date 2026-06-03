import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

os.makedirs('assets', exist_ok=True)  # Dash auto-serves files from /assets

# Glyph color palettes by uncertainty tier
# Outer-to-inner layers
glyphs = {
    'tier_0': ['#FFD700'],                                          # yellow only (low uncertainty)
    'tier_1': ['#FF8C00', '#FFD700'],                                # orange wrapping yellow
    'tier_2': ['#DC143C', '#FF8C00', '#FFD700'],                     # red, orange, yellow
    'tier_3': ['#888888', '#DC143C', '#FF8C00', '#FFD700'],          # grey on top
}

# Fire shape outline (rough flame silhouette)
# We'll use simple concentric circles for clarity
def make_glyph(filename, colors):
    fig, ax = plt.subplots(figsize=(2, 2), dpi=200)
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.patch.set_alpha(0)  # transparent background
    
    # Each layer is a flame shape, shrinking inward
    n = len(colors)
    for i, color in enumerate(colors):
        radius = 1.0 - i * (0.85 / max(n, 1))
        # Flame shape: ellipse stretched vertically with pointed top
        flame = patches.FancyBboxPatch(
            (-radius * 0.7, -radius * 0.9),
            radius * 1.4, radius * 1.8,
            boxstyle=f"round,pad=0.02,rounding_size={radius * 0.5}",
            facecolor=color,
            edgecolor='none'
        )
        ax.add_patch(flame)
    
    plt.savefig(f'assets/{filename}.png', transparent=True, bbox_inches='tight', pad_inches=0)
    plt.close()

for name, colors in glyphs.items():
    make_glyph(name, colors)

print("Done! Glyphs saved to assets/")
print("Files:", os.listdir('assets'))