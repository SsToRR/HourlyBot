# Teams App Manifest

This folder contains the Teams app manifest for importing your bot into Microsoft Teams.

## Files:
- `manifest.json` - The main manifest file
- `outline.png` - Bot icon outline (96x96px)
- `color.png` - Bot icon color (192x192px)

## How to use:

1. **Create icon files**: You need to create two icon files:
   - `outline.png` (96x96 pixels) - Transparent background with bot icon outline
   - `color.png` (192x192 pixels) - Full color bot icon

2. **Update the manifest**:
   - Replace `{{TEAMS_APP_ID}}` with your actual Teams app ID
   - Replace `{{BOT_ID}}` with your bot's Microsoft App ID
   - Update the developer information (name, website, etc.)
   - Update the ngrok URL if it changes

3. **Import to Teams**:
   - Go to https://dev.teams.microsoft.com/
   - Click "Import app"
   - Select the `manifest.json` file
   - The app will be available for testing

## Important Notes:
- Make sure your ngrok URL in the manifest matches your current ngrok tunnel
- The bot must be running and accessible via the ngrok URL
- You may need to update the `validDomains` array if your ngrok URL changes

## Icon Requirements:
- PNG format
- Transparent background for outline.png
- Square dimensions (96x96 for outline, 192x192 for color)
- Should represent your bot's functionality 