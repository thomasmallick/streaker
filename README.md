# Streak Removal Script

A Python script that automatically detects and removes vertical scanner streaks from scanned photos while preserving all other image content.

## Overview

This script identifies thin vertical streaks caused by scanner sensor imperfections and removes them by correcting only the affected columns in the LAB luminance channel. The approach ensures that:

- **Only images with detected streaks are modified**
- **Only the thin streak columns are altered** - surrounding content remains unchanged
- **Fixed images are logged** for manual verification
- **Color information is preserved** through LAB color space processing

## Features

- **Column-only correction**: Modifies only detected streak columns (typically 1-8 pixels wide)
- **Selective processing**: Only writes output files for images with detected streaks
- **LAB color space**: Works on luminance channel only, preserving color information
- **Conservative detection**: Uses statistical outlier detection to avoid false positives
- **Simple logging**: Lists only fixed filenames for easy verification

## Requirements

- Python 3.7+
- OpenCV (`opencv-python`)
- NumPy

### Installation

```bash
pip install opencv-python numpy
```

## Usage

### Basic Usage

```bash
python streaker.py
```

The script will:
1. Process all images in `../data/input/`
2. Detect vertical scanner streaks
3. Fix only images with detected streaks
4. Save corrected images to `../data/output/`
5. Print a summary of fixed filenames

### Output Example

```
FIXED: 1990s_2000s_MattChildhood_0043_a.jpg
FIXED: 2002_YellowstoneTrip_0109_a.jpg
Fixed images: 2
- 1990s_2000s_MattChildhood_0043_a.jpg
- 2002_YellowstoneTrip_0109_a.jpg
```

### Folder Structure

```
Streak-Removal-Script/
├── src/
│   └── streaker.py          # Main script
├── data/
│   ├── input/              # Source images
│   └── output/             # Corrected images (auto-created)
└── README.md
```

## How It Works

### Detection Algorithm

1. **Column Profile Analysis**: Computes median luminance for each column
2. **Baseline Smoothing**: Creates a smoothed baseline across columns
3. **Statistical Outlier Detection**: Identifies columns significantly different from baseline
4. **Consistency Verification**: Ensures detected columns have consistent vertical bias
5. **Run Grouping**: Groups adjacent detected columns into streak runs (max 8 pixels wide)

### Correction Method

1. **LAB Color Space**: Converts image to LAB for perceptually uniform luminance
2. **Column Interpolation**: Replaces each streak column with interpolation of neighboring columns
3. **Color Preservation**: Only modifies L channel, A/B channels remain unchanged
4. **Clamping**: Ensures output values stay within valid LAB range

### Detection Parameters

- **Threshold**: `max(2.0, 4.0 * sigma)` - Statistical outlier threshold
- **Residual Threshold**: `1.0` - Minimum median residual difference
- **Consistency**: `60%` - Minimum percentage of pixels with consistent bias
- **Max Width**: `8` pixels - Maximum streak width to process

## Customization

### Adjusting Detection Sensitivity

If the script misses faint streaks, you can adjust these parameters in `streaker.py`:

```python
# More sensitive detection (lower values)
thresh = max(2.0, 3.0 * sigma)  # Was 4.0 * sigma
if abs(r_med) < 0.5:           # Was 1.0
if float(np.mean(same_sign)) < 0.40:  # Was 0.60
```

### Changing Input/Output Paths

Modify the paths in the `main()` function:

```python
def main():
    input_folder = "path/to/your/input"
    output_folder = "path/to/your/output"
    batch_process_images(input_folder, output_folder)
```

## Supported Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff, .tif)

## Troubleshooting

### No Images Fixed

If you see "Fixed images: 0" but know there are streaks:

1. **Check streak characteristics**: The script targets thin vertical lines (1-8 pixels wide)
2. **Verify streak visibility**: Streaks should be visible as consistent brightness differences
3. **Adjust sensitivity**: See "Customization" section above
4. **Check image quality**: Very low-quality or heavily compressed images may not have detectable patterns

### Overly Aggressive Detection

If the script detects too many false streaks:

1. **Increase thresholds**: Raise the sensitivity parameters in reverse direction
2. **Check image content**: Ensure images don't have natural vertical patterns

### Color Shifts

If you notice color changes:

1. **Check LAB conversion**: Ensure OpenCV version supports LAB properly
2. **Verify input format**: Some formats may need conversion before processing

## Technical Details

### Color Space Choice

LAB color space is used because:
- **L channel** separates luminance from color information
- **Perceptual uniformity** makes brightness corrections more natural
- **Color preservation** by leaving A/B channels untouched

### Statistical Detection

The detection uses robust statistics:
- **Median Absolute Deviation (MAD)** for outlier detection
- **Median-based thresholds** to resist influence from extreme values
- **Consistency checks** to avoid detecting random noise

### Interpolation Method

Linear interpolation between neighboring columns:
- Preserves natural gradients
- Avoids artificial edges
- Maintains image continuity

## License

This script is provided as-is for personal use in correcting scanned family photos.

## Contributing

Feel free to submit issues or pull requests to improve detection accuracy or add new features.
