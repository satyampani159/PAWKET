import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Line, Circle, G, Text as SvgText } from 'react-native-svg';
import { FONTS } from '../constants/theme';

export default function MultiLineChart({
  datasets,    // [{label, color, data: [{x, y}]}]
  labels,      // x-axis labels ["Jul", "Aug", "Sep"]
  width = 320,
  height = 220,
  yPrefix = '\u20B9',
}) {
  const padL = 50, padR = 20, padT = 20, padB = 40;
  const chartW = width - padL - padR;
  const chartH = height - padT - padB;

  // Find Y range across all datasets
  let allY = [];
  datasets.forEach((ds) => ds.data.forEach((d) => allY.push(d.y)));
  const maxY = Math.max(...allY, 1);
  const ySteps = 5;
  const yStepVal = Math.ceil(maxY / ySteps / 1000) * 1000 || 1000;
  const yMax = yStepVal * ySteps;

  // X positions: evenly spaced
  const xCount = labels.length;
  const xStep = chartW / Math.max(xCount - 1, 1);

  function getX(i) {
    return padL + i * xStep;
  }
  function getY(val) {
    return padT + chartH - (val / yMax) * chartH;
  }

  // Format currency short
  function fmtY(v) {
    if (v >= 100000) return `${(v / 100000).toFixed(1)}L`;
    if (v >= 1000) return `${(v / 1000).toFixed(1)}k`;
    return String(v);
  }

  return (
    <View style={[styles.container, { width, height: height + 10 }]}>
      <Svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
        {/* Y-axis grid lines and labels */}
        {Array.from({ length: ySteps + 1 }, (_, i) => {
          const val = i * yStepVal;
          const y = getY(val);
          return (
            <G key={`y${i}`}>
              <Line x1={padL} y1={y} x2={width - padR} y2={y} stroke="#23272F" strokeWidth={1} />
              <SvgText
                x={padL - 8}
                y={y + 4}
                textAnchor="end"
                fontSize={10}
                fill="#4A5060"
                fontWeight="500"
              >
                {fmtY(val)}
              </SvgText>
            </G>
          );
        })}

        {/* X-axis labels */}
        {labels.map((label, i) => (
          <SvgText
            key={`x${i}`}
            x={getX(i)}
            y={height - 8}
            textAnchor="middle"
            fontSize={11}
            fill="#8B919E"
            fontWeight="600"
          >
            {label}
          </SvgText>
        ))}

        {/* Data lines and points */}
        {datasets.map((ds, di) => {
          if (!ds.data || ds.data.length === 0) return null;
          const points = ds.data.map((d, i) => ({ x: getX(i), y: getY(d.y) }));

          return (
            <G key={di}>
              {points.map((p, i) => {
                if (i === 0) return null;
                return (
                  <Line
                    key={`${di}-${i}`}
                    x1={points[i - 1].x}
                    y1={points[i - 1].y}
                    x2={p.x}
                    y2={p.y}
                    stroke={ds.color}
                    strokeWidth={2.5}
                    strokeLinecap="round"
                  />
                );
              })}

              {/* Points and data labels */}
              {points.map((p, i) => (
                <G key={`${di}-p${i}`}>
                  <Circle cx={p.x} cy={p.y} r={4} fill={ds.color} />
                  <Circle cx={p.x} cy={p.y} r={2} fill="#FFFFFF" />
                  {/* Data label */}
                  <SvgText
                    x={p.x}
                    y={p.y - 10}
                    textAnchor="middle"
                    fontSize={10}
                    fill={ds.color}
                    fontWeight="700"
                  >
                    {yPrefix}{fmtY(ds.data[i].y)}
                  </SvgText>
                </G>
              ))}
            </G>
          );
        })}
      </Svg>

      {/* Dataset legend */}
      <View style={styles.legend}>
        {datasets.map((ds, i) => (
          <View key={i} style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: ds.color }]} />
            <Text style={styles.legendLabel} numberOfLines={1}>{ds.label}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: 'center' },
  legend: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginTop: 8,
    gap: 12,
  },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  legendDot: { width: 8, height: 8, borderRadius: 4 },
  legendLabel: {
    color: '#8B919E',
    fontSize: 11,
    ...FONTS.medium,
  },
});
