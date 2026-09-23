// src/services/smsReader.js
import { Platform, NativeModules, DeviceEventEmitter } from 'react-native';

const FINANCIAL_KEYWORDS = [
  'debited', 'credited', 'inr', 'rs.', 'rs ', '₹',
  'upi', 'neft', 'imps', 'atm', 'balance',
  'payment', 'transaction', 'emi', 'loan',
  'debit', 'credit', 'withdraw', 'transfer',
  'paytm', 'phonepe', 'gpay', 'simpl', 'lazypay',
  'a/c', 'acct', 'account', 'bank',
];

function looksFinancial(body) {
  if (!body) return false;
  const text = body.toLowerCase();
  for (const kw of FINANCIAL_KEYWORDS) {
    if (text.includes(kw)) return true;
  }
  return false;
}

export async function readSMSAndroid(daysBack = 90) {
  if (Platform.OS !== 'android') return [];

  const minDate = Date.now() - daysBack * 24 * 60 * 60 * 1000;

  return new Promise((resolve) => {
    try {
      // Try react-native-get-sms-android
      const SmsAndroid = require('react-native-get-sms-android').default;

      SmsAndroid.list(
        JSON.stringify({
          box:      'inbox',
          minDate:  minDate,
          maxCount: 5000,
        }),
        (fail) => {
          console.warn('[SMS] Read failed:', fail);
          resolve([]);
        },
        (count, smsList) => {
          try {
            const parsed  = JSON.parse(smsList);
            const financial = parsed.filter(s => looksFinancial(s.body));
            const result = financial.map(sms => ({
              smsId:      String(sms._id),
              text:       sms.body,
              sender:     sms.address,
              receivedAt: new Date(parseInt(sms.date)).toISOString(),
            }));
            console.log(`[SMS] Read ${count} total, ${result.length} financial`);
            resolve(result);
          } catch (e) {
            console.warn('[SMS] Parse error:', e.message);
            resolve([]);
          }
        }
      );
    } catch (e) {
      console.warn('[SMS] Module load error:', e.message);
      resolve([]);
    }
  });
}
