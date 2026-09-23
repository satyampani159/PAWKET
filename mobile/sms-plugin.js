// sms-plugin.js
// Custom Expo config plugin to properly add SMS reading to Android
const { withAndroidManifest } = require('@expo/config-plugins');

module.exports = function withSMSPermissions(config) {
  return withAndroidManifest(config, async (config) => {
    const androidManifest = config.modResults;
    const mainApplication = androidManifest.manifest;

    // Add SMS permissions if not already there
    const permissions = mainApplication['uses-permission'] || [];
    
    const smsPermissions = [
      'android.permission.READ_SMS',
      'android.permission.RECEIVE_SMS',
    ];

    smsPermissions.forEach(permission => {
      const exists = permissions.some(
        p => p.$?.['android:name'] === permission
      );
      if (!exists) {
        permissions.push({
          $: { 'android:name': permission }
        });
      }
    });

    mainApplication['uses-permission'] = permissions;
    return config;
  });
};
