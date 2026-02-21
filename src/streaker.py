import cv2
import numpy as np
import os

def remove_streaks(image_path, output_path):
    # Read the image
    img = cv2.imread(image_path)
    if img is None:
        return False, []

    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
    l_chan = lab[:, :, 0]
    h, w = l_chan.shape

    col_profile = np.median(l_chan, axis=0)
    k = min(51, w if w % 2 == 1 else w - 1)
    if k < 3:
        return False, []
    if k % 2 == 0:
        k -= 1
    smooth = cv2.GaussianBlur(col_profile.reshape(1, -1), (k, 1), 0).reshape(-1)
    delta = col_profile - smooth

    delta_med = float(np.median(delta))
    mad = float(np.median(np.abs(delta - delta_med)))
    sigma = 1.4826 * mad if mad > 0 else float(np.std(delta))
    thresh = max(1.5, 3.0 * sigma)  # More sensitive

    candidates = np.where(np.abs(delta - delta_med) > thresh)[0]
    candidates = candidates[(candidates >= 2) & (candidates <= w - 3)]

    good_cols = []
    for x in candidates.tolist():
        residual = l_chan[:, x] - 0.5 * (l_chan[:, x - 1] + l_chan[:, x + 1])
        r_med = float(np.median(residual))
        if abs(r_med) < 0.3:  # More sensitive for faint streaks
            continue
        strong = np.abs(residual) > 0.3  # More sensitive for faint streaks
        if not np.any(strong):
            continue
        same_sign = (np.sign(residual) == np.sign(r_med)) & strong
        if float(np.mean(same_sign)) < 0.25:  # More lenient for partial streaks
            continue
        
        # Check if the streak covers a reasonable portion of the height
        strong_rows = np.sum(strong)
        height_ratio = strong_rows / h
        if height_ratio < 0.2:  # At least 20% of image height
            continue
            
        good_cols.append(x)

    if not good_cols:
        return False, []

    good_cols = sorted(set(good_cols))
    runs = []
    start = end = good_cols[0]
    for x in good_cols[1:]:
        if x == end + 1:
            end = x
        else:
            runs.append((start, end))
            start = end = x
    runs.append((start, end))

    runs = [(s, e) for (s, e) in runs if (e - s + 1) <= 8]
    if not runs:
        return False, []

    l_fixed = l_chan.copy()
    for s, e in runs:
        left = s - 1
        right = e + 1
        if left < 0 and right >= w:
            continue
        for x in range(s, e + 1):
            if left < 0:
                l_fixed[:, x] = l_chan[:, right]
            elif right >= w:
                l_fixed[:, x] = l_chan[:, left]
            else:
                t = (x - left) / (right - left)
                l_fixed[:, x] = (1.0 - t) * l_chan[:, left] + t * l_chan[:, right]
                
                # Additional correction for partial streaks:
                # Only modify rows where the streak is actually present
                residual = l_chan[:, x] - 0.5 * (l_chan[:, x - 1] + l_chan[:, x + 1])
                streak_rows = np.abs(residual) > 0.5
                if np.any(streak_rows):
                    # Apply correction only to streak rows
                    l_fixed[streak_rows, x] = (1.0 - t) * l_chan[streak_rows, left] + t * l_chan[streak_rows, right]

    lab[:, :, 0] = np.clip(l_fixed, 0, 255)
    fixed_bgr = cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)

    cv2.imwrite(output_path, fixed_bgr)
    return True, runs

def generate_heatmaps(input_folder, output_folder, diff_folder):
    """Create visual difference maps using the same detection logic as streak removal"""
    
    if not os.path.exists(diff_folder):
        os.makedirs(diff_folder)
    
    for filename in os.listdir(input_folder):
        if not filename.lower().endswith(('.jpg', '.png', '.jpeg')):
            continue
            
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)
        
        if not os.path.exists(output_path):
            continue
            
        # Read images
        original = cv2.imread(input_path)
        corrected = cv2.imread(output_path)
        
        if original is None or corrected is None:
            continue
        
        # Use LAB space for more accurate change detection
        orig_lab = cv2.cvtColor(original, cv2.COLOR_BGR2LAB).astype(np.float32)
        corr_lab = cv2.cvtColor(corrected, cv2.COLOR_BGR2LAB).astype(np.float32)
        
        # Calculate difference in L channel (same as validation)
        l_diff = np.abs(orig_lab[:, :, 0] - corr_lab[:, :, 0])
        
        # Find columns with significant changes (same threshold as validation)
        col_changes = np.mean(l_diff, axis=0)
        changed_cols = np.where(col_changes > 1.0)[0]
        
        # Create heatmap showing only the actual changed pixels (not entire columns)
        heatmap = np.zeros_like(original)
        
        # For each changed column, find the specific rows that were modified
        for col in changed_cols:
            # Find which rows in this column actually changed significantly
            col_diff = l_diff[:, col]
            changed_rows = np.where(col_diff > 1.0)[0]  # Same threshold as column detection
            
            # Highlight only the changed rows in this column
            if len(changed_rows) > 0:
                # Use red intensity based on change magnitude
                for row in changed_rows:
                    change_intensity = np.clip(col_diff[row] / 20.0, 0, 1)  # Normalize to 0-1
                    heatmap[row, col, 2] = int(255 * change_intensity)  # Red channel
        
        # Save difference map
        diff_path = os.path.join(diff_folder, f"diff_{filename}")
        cv2.imwrite(diff_path, heatmap)
        
        # Calculate statistics using actual changed pixels (not entire columns)
        total_changed_pixels = 0
        for col in changed_cols:
            col_diff = l_diff[:, col]
            changed_rows = np.where(col_diff > 1.0)[0]
            total_changed_pixels += len(changed_rows)
        
        if total_changed_pixels > 0:
            total_pixels = original.shape[0] * original.shape[1]
            change_percentage = (total_changed_pixels / total_pixels) * 100
            
            print(f"📸 {filename}: {total_changed_pixels:,} pixels actually changed ({change_percentage:.3f}%)")
            print(f"   Heatmap saved: diff_{filename}")
        else:
            print(f"📸 {filename}: No significant changes detected")
            print(f"   No heatmap generated")

def validate_changes(input_folder, output_folder):
    """Validate that only streak columns were modified"""
    
    for filename in os.listdir(input_folder):
        if not filename.lower().endswith(('.jpg', '.png', '.jpeg')):
            continue
            
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)
        
        if not os.path.exists(output_path):
            continue
            
        # Read both images
        original = cv2.imread(input_path)
        corrected = cv2.imread(output_path)
        
        if original is None or corrected is None:
            continue
            
        # Convert to LAB for perceptual comparison
        orig_lab = cv2.cvtColor(original, cv2.COLOR_BGR2LAB).astype(np.float32)
        corr_lab = cv2.cvtColor(corrected, cv2.COLOR_BGR2LAB).astype(np.float32)
        
        # Calculate difference in L channel
        l_diff = np.abs(orig_lab[:, :, 0] - corr_lab[:, :, 0])
        
        # Find columns with significant changes
        col_changes = np.mean(l_diff, axis=0)
        changed_cols = np.where(col_changes > 1.0)[0]  # Threshold for meaningful change
        
        if len(changed_cols) == 0:
            print(f"✓ {filename}: No significant changes detected")
            continue
            
        # Group changed columns into runs
        runs = []
        if len(changed_cols) > 0:
            start = end = changed_cols[0]
            for col in changed_cols[1:]:
                if col == end + 1:
                    end = col
                else:
                    runs.append((start, end))
                    start = end = col
            runs.append((start, end))
        
        # Calculate statistics
        total_pixels = original.shape[0] * original.shape[1]
        changed_pixels = len(changed_cols) * original.shape[0]
        change_percentage = (changed_pixels / total_pixels) * 100
        
        # Maximum change per column
        max_changes = [np.max(l_diff[:, col]) for col in changed_cols]
        avg_max_change = np.mean(max_changes) if max_changes else 0
        
        print(f"\n📊 {filename}:")
        print(f"   Changed columns: {len(changed_cols)}")
        print(f"   Column runs: {runs}")
        print(f"   Pixels modified: {changed_pixels:,} ({change_percentage:.2f}%)")
        print(f"   Max L change per column: {avg_max_change:.1f}")
        
        # Validate color preservation
        a_diff = np.mean(np.abs(orig_lab[:, :, 1] - corr_lab[:, :, 1]))
        b_diff = np.mean(np.abs(orig_lab[:, :, 2] - corr_lab[:, :, 2]))
        
        if a_diff < 0.1 and b_diff < 0.1:
            print(f"   ✓ Color channels preserved (A: {a_diff:.3f}, B: {b_diff:.3f})")
        else:
            print(f"   ⚠️  Color channels changed (A: {a_diff:.3f}, B: {b_diff:.3f})")
        
        # Check if changes are column-only
        non_column_pixels = 0
        for row in range(original.shape[0]):
            for col in range(original.shape[1]):
                if col not in changed_cols and l_diff[row, col] > 1.0:
                    non_column_pixels += 1
        
        if non_column_pixels == 0:
            print(f"   ✓ Changes are column-only")
        else:
            print(f"   ⚠️  {non_column_pixels} pixels changed outside detected columns")

def batch_process_images(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    fixed_files = []

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(('.jpg', '.png', '.jpeg')):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)
            fixed, runs = remove_streaks(input_path, output_path)
            if fixed:
                fixed_files.append(filename)
                print(f"FIXED: {filename}")

    print(f"Fixed images: {len(fixed_files)}")
    for name in fixed_files:
        print(f"- {name}")

def main():
    input_folder = "../data/input"  # Change to your folder path
    output_folder = "../data/output"
    diff_folder = "../data/differences"
    
    print("=== STREAK REMOVAL PROCESSING ===")
    batch_process_images(input_folder, output_folder)
    
    print("\n=== VISUAL DIFFERENCE HEATMAPS ===")
    generate_heatmaps(input_folder, output_folder, diff_folder)
    
    print("\n=== VALIDATION RESULTS ===")
    validate_changes(input_folder, output_folder)
    
    print("\n=== PROCESSING COMPLETE ===")

if __name__ == "__main__":
    main()
