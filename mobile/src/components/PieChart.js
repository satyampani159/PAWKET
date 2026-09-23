import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Path, G } from 'react-native-svg';
import { FONTS } from '../constants/theme';

function polarToCartesian(cx, cy, r, angleDeg) {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

export default function PieChart({
  data,       // [{label, value, color}]
  size = 220,
  innerRadius = 0.55, // donut hole ratio
  centerLabel,
  centerValue,
}) {
  const total = data.reduce((s, d) => s + d.value, 0) || 1;
  const cx = size / 2;
  const cy = size / 2;
  const outerR = size / 2 - 30; // leave room for labels outside
  const innerR = outerR * innerRadius;

  let cumAngle = 0;
  const slices = data
    .filter((d) => d.value > 0)
    .map((d) => {
      const pct = (d.value / total) * 100;
      const angle = (d.value / total) * 360;
      const startAngle = cumAngle;
      const endAngle = cumAngle + angle;
      const midAngle = startAngle + angle / 2;
      cumAngle = endAngle;

      return { ...d, startAngle, endAngle, midAngle, pct };
    });

  return (
    <View style={[styles.container, { width: size, height: size + 80 }]}>
      <Svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <G>
          {slices.map((s, i) => {
            const outerStart = polarToCartesian(cx, cy, outerR, s.startAngle);
            const outerEnd = polarToCartesian(cx, cy, outerR, s.endAngle);
            const innerStart = polarToCartesian(cx, cy, innerR, s.startAngle);
            const innerEnd = polarToCartesian(cx, cy, innerR, s.endAngle);
            const largeArc = s.endAngle - s.startAngle > 180 ? 1 : 0;

            const path = [
              `M ${outerStart.x} ${outerStart.y}`,
              `A ${outerR} ${outerR} 0 ${largeArc} 1 ${outerEnd.x} ${outerEnd.y}`,
              `L ${innerEnd.x} ${innerEnd.y}`,
              `A ${innerR} ${innerR} 0 ${largeArc} 0 ${innerStart.x} ${innerStart.y}`,
              'Z',
            ].join(' ');

            return <Path key={i} d={path} fill={s.color} />;
          })}
        </G>
      </Svg>

      {/* Center text as React Native Text overlay */}
      {centerValue != null && (
        <View style={{ position: 'absolute', alignSelf: 'center', top: cx - innerR, width: innerR * 2, height: innerR * 2, alignItems: 'center', justifyContent: 'center' }}>
          <Text style={styles.centerValue} numberOfLines={1}>{centerValue}</Text>
          {centerLabel && <Text style={styles.centerSub} numberOfLines={1}>{centerLabel}</Text>}
        </View>
      )}

      {/* Legend */}
      <View style={styles.legend}>
        {slices.map((s, i) => (
          <View key={i} style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: s.color }]} />
            <Text style={styles.legendLabel} numberOfLines={1}>
              {s.label}
            </Text>
            <Text style={styles.legendValue} numberOfLines={1}>
              {'\u20B9'}{s.value.toLocaleString('en-IN')} ({s.pct.toFixed(0)}%)
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: 'center' },
  centerValue: {
    color: '#FFFFFF',
    fontSize: 16,
    ...FONTS.bold,
    textAlign: 'center',
  },
  centerSub: {
    color: '#8B919E',
    fontSize: 10,
    textAlign: 'center',
    marginTop: 2,
  },
  legend: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginTop: 12,
    gap: 6,
    paddingHorizontal: 4,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#161921',
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
    gap: 4,
  },
  legendDot: { width: 8, height: 8, borderRadius: 4 },
  legendLabel: {
    color: '#8B919E',
    fontSize: 11,
    ...FONTS.medium,
  },
  legendValue: {
    color: '#FFFFFF',
    fontSize: 11,
    ...FONTS.semi,
  },
});
