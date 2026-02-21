# Windsurf Rules for Streak Removal Script

## Core Principles

1. **Preserve Original Intent**: The script should only modify thin vertical streak columns and preserve all other image content
2. **Selective Processing**: Only write output files for images with detected streaks
3. **Minimal Logging**: Keep console output concise, listing only fixed filenames
4. **Color Preservation**: Use LAB color space to modify only luminance channel

## Development Rules

### Code Changes
- Any modification to detection algorithm, correction method, or core functionality MUST include updating the README.md
- Maintain column-only correction approach - do not introduce broad inpainting or region-based modifications
- Preserve the statistical outlier detection methodology unless explicitly replacing with a better approach
- Keep the selective processing behavior (only fix images with detected streaks)

### README Updates Required When:
- Changing detection algorithm or parameters
- Modifying correction method or color space usage
- Adding new features or capabilities
- Changing input/output behavior
- Updating supported file formats
- Modifying logging output format

### README Update Checklist:
- [ ] Update "How It Works" section if algorithm changes
- [ ] Update "Customization" section if parameters change
- [ ] Update "Features" section if capabilities change
- [ ] Update "Troubleshooting" section if new issues arise
- [ ] Update version/date if significant changes

### Code Style
- Use descriptive variable names
- Add comments for complex detection logic
- Maintain consistent error handling
- Keep functions focused and modular

### Testing
- Test with images that have visible streaks
- Verify only streak columns are modified
- Confirm clean images are not processed
- Check color preservation in corrected areas

## Prohibited Changes
- Do not remove selective processing behavior
- Do not introduce broad image modifications
- Do not change the core column-only correction approach
- Do not add verbose debug logging to main output

## Quality Gates
Before committing changes:
1. Does this change the script's functionality? → Update README
2. Does this affect detection behavior? → Update README
3. Does this modify correction method? → Update README
4. Does this change user-facing behavior? → Update README
