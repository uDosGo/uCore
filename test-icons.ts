// Test file to verify icon changes
import { Icon } from './src/components/Icon';

// Test the new icons
const testIcons = [
  'hamburger',      // 🍔 SnackShack
  'fastfood',       // 🍟 SnackMachine  
  'smile',          // 😊 Happy UI Hub
  'sad',            // 😢 Sad UI Hub
  'content_paste_go', // 💥 Clipboard boom
];

console.log('Testing new icons:', testIcons);

// Verify icons are in the map
import { iconMap } from './src/components/Icon';
for (const iconName of testIcons) {
  if (iconMap[iconName]) {
    console.log(`✓ Icon "${iconName}" found: ${iconMap[iconName].name}`);
  } else {
    console.log(`✗ Icon "${iconName}" NOT found`);
  }
}